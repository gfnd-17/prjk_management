from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
import requests
import logging

_logger = logging.getLogger(__name__)


class ProjectManagement(models.Model):
    _name = 'project.management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Manajemen Proyek'

    project_number = fields.Char(string='Nomor Proyek', required=True,
                                 copy=False, readonly=True, index=True, default=lambda self: _('New'))
    name = fields.Char(string='Nama Proyek', required=True,
                       track_visibility='onchange')
    description = fields.Text(string='Deskripsi')
    owner_id = fields.Many2one('res.users', string='Pemilik Proyek',
                               required=True, default=lambda self: self.env.user)
    start_date = fields.Date(string='Tanggal Mulai',
                             required=True, track_visibility='onchange')
    end_date = fields.Date(string='Tanggal Selesai',
                           required=True, track_visibility='onchange')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('aktif', 'Aktif'),
        ('selesai', 'Selesai'),
        ('ditangguhkan', 'Ditangguhkan'),
    ], string='Status', default='draft', readonly=True, required=True, track_visibility='onchange')
    duration = fields.Integer(string='Durasi (hari)',
                              compute='_compute_duration', store=True)
    remaining_days = fields.Integer(
        string='Sisa Durasi (hari)', compute='_compute_remaining_days', store=True)
    trello_board_id = fields.Char(string='Trello Board ID')
    trello_todo_list_id = fields.Char(string="Trello To Do List ID")
    trello_doing_list_id = fields.Char(string="Trello Doing List ID")
    trello_done_list_id = fields.Char(string="Trello Done List ID")
    trello_card_id = fields.Char(string="Trello Card ID")

    def write(self, vals):
        """Cegah edit jika proyek sudah di-post (status='aktif')."""
        for rec in self:
            if rec.status == 'aktif' and any(field in vals for field in ['name', 'description', 'start_date', 'end_date', 'owner_id']):
                raise ValidationError(
                    "Proyek yang sudah dipost tidak bisa diedit lagi!")
        return super(ProjectManagement, self).write(vals)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.end_date < rec.start_date:
                    raise ValidationError(
                        "Tanggal Selesai tidak boleh kurang dari Tanggal Mulai.")

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                start = fields.Date.from_string(rec.start_date)
                end = fields.Date.from_string(rec.end_date)
                rec.duration = (end - start).days
            else:
                rec.duration = 0

    @api.depends('end_date')
    def _compute_remaining_days(self):
        """Menghitung sisa durasi dari hari ini sampai tanggal selesai"""
        for rec in self:
            if rec.end_date:
                today = fields.Date.context_today(self)
                end_date = fields.Date.from_string(rec.end_date)
                rec.remaining_days = (end_date - today).days
                if rec.remaining_days < 0:
                    rec.remaining_days = 0
            else:
                rec.remaining_days = 0

    def action_post(self):
        """Mengubah status dari draft atau ditangguhkan menjadi aktif."""
        for rec in self:
            if rec.status in ('draft', 'ditangguhkan'):
                old_status = rec.status
                rec.status = 'aktif'
                rec._send_status_notification(old_status, 'aktif')
                rec.move_trello_card('aktif')
                rec.message_post(
                    body=f"Status berubah dari {old_status} ke Aktif pada {fields.Datetime.now()}.")

    def action_suspend(self):
        """Mengubah status dari aktif menjadi ditangguhkan."""
        for rec in self:
            if rec.status == 'aktif':
                old_status = rec.status
                rec.status = 'ditangguhkan'
                rec._send_status_notification(old_status, 'ditangguhkan')
                rec.move_trello_card('ditangguhkan')
                rec.message_post(
                    body=f"Status berubah dari {old_status} ke Ditangguhkan pada {fields.Datetime.now()}.")

    def action_batal(self):
        """Mengembalikan status dari aktif atau ditangguhkan kembali ke draft."""
        for rec in self:
            if rec.status in ('aktif', 'ditangguhkan'):
                old_status = rec.status
                rec.status = 'draft'
                rec._send_status_notification(old_status, 'draft')
                rec.move_trello_card('draft')
                rec.message_post(
                    body=f"Status berubah dari {old_status} ke Draft pada {fields.Datetime.now()}.")

    @api.model
    def update_project_status(self):
        """Update otomatis: jika tanggal saat ini >= end_date dan status masih 'aktif', ubah menjadi 'selesai'."""
        today = fields.Date.context_today(self)
        batch_size = 50

        project_ids = self.search(
            [('status', '=', 'aktif'), ('end_date', '<=', today)], limit=batch_size)

        while project_ids:
            for rec in project_ids:
                old_status = rec.status
                rec.status = 'selesai'
                rec._send_status_notification(old_status, 'selesai')
                rec.move_trello_card('selesai')
                rec.message_post(
                    body=f"Status berubah dari {old_status} ke Selesai secara otomatis pada {fields.Datetime.now()}.")

            self.env.cr.commit()
            project_ids = self.search(
                [('status', '=', 'aktif'), ('end_date', '<=', today)], limit=batch_size)

    def _send_status_notification(self, old_status, new_status):
        """Mengirim notifikasi email saat terjadi perubahan status proyek ke email tetap."""
        template = self.env.ref(
            'project_management.email_template_project_status', raise_if_not_found=False)
        if not template:
            _logger.error(
                "Template email tidak ditemukan! Pastikan ID template sesuai di mail_template_data.xml")
            return

        for rec in self:
            email_values = {
                'email_to': 'govindo1706@gmail.com',
            }
            template.with_context(old_status=old_status, new_status=new_status).send_mail(
                rec.id, force_send=True, email_values=email_values
            )

    @property
    def trello_api_key(self):
        return self.env['ir.config_parameter'].sudo().get_param('trello.api_key', '')

    @property
    def trello_token(self):
        return self.env['ir.config_parameter'].sudo().get_param('trello.token', '')

    @api.model
    def create(self, vals):
        """Override create untuk memastikan nomor proyek tetap terbuat & integrasi Trello berjalan"""

        # Generate nomor proyek menggunakan ir.sequence
        if vals.get('project_number', 'New') == 'New':
            vals['project_number'] = self.env['ir.sequence'].next_by_code(
                'project.management') or 'New'

        project = super(ProjectManagement, self).create(vals)
        if not project.trello_board_id:
            board_id = project.create_trello_board(vals['name'])
            project.trello_board_id = board_id

        if not project.trello_todo_list_id:
            project.trello_todo_list_id = project.create_trello_list(
                board_id, "To Do")
        if not project.trello_doing_list_id:
            project.trello_doing_list_id = project.create_trello_list(
                board_id, "Doing")
        if not project.trello_done_list_id:
            project.trello_done_list_id = project.create_trello_list(
                board_id, "Done")

        if not project.trello_card_id:
            project.trello_card_id = project.create_trello_card(
                project.name, project.description or '', project.trello_todo_list_id)

        return project

    def create_trello_board(self, board_name):
        url = "https://api.trello.com/1/boards/"
        params = {
            "name": board_name,
            "key": self.trello_api_key,
            "token": self.trello_token
        }

        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
            return response.json().get('id')

        except requests.exceptions.RequestException as e:
            _logger.error(f"Error saat membuat board Trello: {e}")
            return None

    def create_trello_list(self, board_id, list_name):
        """Cek apakah list sudah ada, jika tidak baru buat."""
        url = f"https://api.trello.com/1/boards/{board_id}/lists"
        params = {"key": self.trello_api_key, "token": self.trello_token}
        response = requests.get(url, params=params)

        if response.status_code == 200:
            lists = response.json()
            for trello_list in lists:
                if trello_list['name'] == list_name:
                    return trello_list['id']

        # Jika belum ada, buat list baru
        url = "https://api.trello.com/1/lists"
        params.update({"name": list_name, "idBoard": board_id})
        response = requests.post(url, params=params)

        if response.status_code == 200:
            return response.json().get('id')
        return None

    def create_trello_card(self, card_name, description, list_id):
        """Membuat kartu di Trello List tertentu"""
        if not list_id:
            return False

        url = "https://api.trello.com/1/cards"
        params = {
            "name": card_name,
            "desc": description,
            "idList": list_id,
            "key": self.trello_api_key,
            "token": self.trello_token
        }
        response = requests.post(url, params=params)
        if response.status_code == 200:
            return response.json().get('id')
        return None

    def move_trello_card(self, new_status):
        """Memindahkan kartu ke List yang sesuai berdasarkan status proyek"""
        if not self.trello_card_id:
            return False

        # Tentukan list ID berdasarkan status proyek
        list_id = None
        if new_status in ('draft', 'ditangguhkan'):
            list_id = self.trello_todo_list_id
        elif new_status == 'aktif':
            list_id = self.trello_doing_list_id
        elif new_status == 'selesai':
            list_id = self.trello_done_list_id

        if not list_id:
            return False

        url = f"https://api.trello.com/1/cards/{self.trello_card_id}"
        params = {
            "idList": list_id,
            "key": self.trello_api_key,
            "token": self.trello_token
        }

        response = requests.put(url, params=params)
        return response.status_code == 200

    @api.model
    def sync_status_from_trello(self):
        """Menyinkronkan status proyek dari Trello ke Odoo."""
        projects = self.search(
            [('trello_card_id', '!=', False)])

        for rec in projects:
            url = f"https://api.trello.com/1/cards/{rec.trello_card_id}"
            params = {
                "key": self.trello_api_key,
                "token": self.trello_token
            }
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                trello_data = response.json()
                list_id = trello_data.get('idList')

                # Cocokkan status berdasarkan list ID
                new_status = 'draft'
                if list_id == rec.trello_doing_list_id:
                    new_status = 'aktif'
                elif list_id == rec.trello_done_list_id:
                    new_status = 'selesai'

                if rec.status != new_status:
                    old_status = rec.status
                    rec.status = new_status
                    rec.message_post(
                        body=f"Status proyek diperbarui dari Trello: {old_status} → {new_status}")

            except requests.exceptions.RequestException as e:
                _logger.error(f"Error saat mengambil data dari Trello: {e}")
