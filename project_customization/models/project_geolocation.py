# Copyright (C) 2019, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models,api,_
from odoo.tools import config
from collections import defaultdict
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

ADDRESS_FIELDS = ('city', 'state_id', 'country_id')

class ProjectGeolocation(models.Model):
    _name = "project.geolocation"
    _rec_name = 'point'
    _description = 'ProjectGeolocation'
    _order = 'point desc'
    project_id = fields.Many2one('project.project', string='Projet')
    company_id = fields.Many2one(related="project_id.company_id")
    # address fields
    point = fields.Char(string="Point", required=True)
    street = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char(string="Mouqataa")
    state_id = fields.Many2one("res.country.state", string='Wilaya', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]", required=True)
    country_id = fields.Many2one('res.country', string='Pays', ondelete='restrict', required=True)
    country_code = fields.Char(related='country_id.code', string="Code Pays")
    latitude = fields.Float(string='Geo Latitude', required=True, digits=(10, 15))
    longitude = fields.Float(string='Geo Longitude', required=True, digits=(10, 15))
    date_localization = fields.Date(string='Date Geolocalisation')

    display_address = fields.Char(compute='_compute_display_address', store=True,string="Adresse complète",readonly=False)
    

    @api.onchange('street', 'zip', 'city', 'state_id', 'country_id')
    def _delete_coordinates(self):
        self.latitude = False
        self.longitude = False

    @api.depends('street', 'zip', 'city', 'state_id','country_id')
    def _compute_display_address(self):
        for record in self:
            record.display_address = ''
            if record.street:
                record.display_address += record.street + ', '
            if record.zip:
                record.display_address += record.zip + ', '
            if record.city:
                record.display_address += record.city + ', '
            if record.state_id:
                record.display_address += record.state_id.name + ', '
            if record.country_id:
                record.display_address += record.country_id.name
            record.display_address = record.display_address.strip().strip(',')



    def write(self, vals):
        # Reset latitude/longitude in case we modify the address without
        # updating the related geolocation fields
        if any(field in vals for field in ['city', 'state_id', 'country_id']) \
                and not all('%s' % field in vals for field in ['latitude', 'longitude']):
            vals.update({
                'latitude': 0.0,
                'longitude': 0.0,
            })
        return super().write(vals)

    @api.model
    def _geo_localize(self, street='', zip='', city='', state='', country=''):
        geo_obj = self.env['base.geocoder']
        search = geo_obj.geo_query_address(street=street, zip=zip, city=city, state=state, country=country)
        result = geo_obj.geo_find(search, force_country=country)
        if result is None:
            search = geo_obj.geo_query_address(city=city, state=state, country=country)
            result = geo_obj.geo_find(search, force_country=country)
        return result
    def geo_localize(self):
        # We need country names in English below
        if not self._context.get('force_geo_localize') \
                and (self._context.get('import_file') \
                     or any(config[key] for key in ['test_enable', 'test_file', 'init', 'update'])):
            return False
        partners_not_geo_localized = self.env['project.geolocation']
        for partner in self.with_context(lang='en_US'):
            result = self._geo_localize(partner.street,
                                        partner.zip,
                                        partner.city,
                                        partner.state_id.name,
                                        partner.country_id.name)

            if result:
                partner.write({
                    'latitude': result[0],
                    'longitude': result[1],
                    'date_localization': fields.Date.context_today(partner)
                })
            else:
                partners_not_geo_localized |= partner
        if partners_not_geo_localized:
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'type': 'danger',
                'title': _("Warning"),
                'message': _('No match found for %(partner_names)s address(es).', partner_names=', '.join(partners_not_geo_localized.mapped('display_address')))
            })
        return True


    @api.model
    def _address_fields(self):
        """Returns the list of address fields that are synced from the parent."""
        return list(ADDRESS_FIELDS)

    @api.model
    def _formatting_address_fields(self):
        """Returns the list of address fields usable to format addresses."""
        return self._address_fields()
    @api.model
    def _get_default_address_format(self):
        return "%(city)s %(state_code)s\n%(country_name)s"

    @api.model
    def _get_address_format(self):
        return self.country_id.address_format or self._get_default_address_format()
    def _get_country_name(self):
        return self.country_id.name or ''
    def _prepare_display_address(self, without_company=False):
        # get the information that will be injected into the display format
        # get the address format
        address_format = self._get_address_format()
        args = defaultdict(str, {
            'state_code': self.state_id.code or '',
            'state_name': self.state_id.name or '',
            'country_code': self.country_id.code or '',
            'country_name': self._get_country_name(),
            'company_name': self.company_id.name or '',
        })
        for field in self._formatting_address_fields():
            args[field] = getattr(self, field) or ''
        if without_company:
            args['company_name'] = ''
        elif self.company_id:
            address_format = '%(company_name)s\n' + address_format
        return address_format, args

    def _display_address(self, without_company=False):
        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param without_company: if address contains company
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''
        address_format, args = self._prepare_display_address(without_company)
        return address_format % args

    def _display_address_depends(self):
        # field dependencies of method _display_address()
        return self._formatting_address_fields() + [
            'country_id', 'company_name', 'state_id',
        ]
