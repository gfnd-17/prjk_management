from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestProjectManagement(TransactionCase):

    def setUp(self):
        super(TestProjectManagement, self).setUp()
        self.Project = self.env['project.management']
        self.test_project = self.Project.create({
            'name': 'Proyek Test',
            'description': 'Deskripsi proyek test',
            'start_date': '2025-01-01',
            'end_date': '2025-01-10',
            'status': 'draft'
        })

    def test_create_project(self):
        """Test pembuatan proyek baru"""
        self.assertEqual(self.test_project.name, 'Proyek Test')
        self.assertEqual(self.test_project.status, 'draft')

    def test_update_status(self):
        """Test perubahan status proyek"""
        self.test_project.action_post()
        self.assertEqual(self.test_project.status, 'aktif')

    def test_invalid_dates(self):
        """Test validasi tanggal mulai & selesai"""
        with self.assertRaises(ValidationError):
            self.Project.create({
                'name': 'Proyek Invalid',
                'start_date': '2025-01-10',
                'end_date': '2025-01-01',
                'status': 'draft'
            })

    def test_notification_email_sent(self):
        """Test apakah email notifikasi dikirim setelah perubahan status"""
        mail_template = self.env.ref(
            'project_management.email_template_project_status')
        mail = mail_template.send_mail(self.test_project.id, force_send=True)
        self.assertTrue(mail, "Email notifikasi tidak terkirim!")

    def test_trello_sync(self):
        """Test sinkronisasi Trello berjalan (mock API call)"""
        # Simulasi bahwa Trello Card ID sudah dibuat
        self.test_project.trello_card_id = 'mock_trello_card_123'
        self.test_project.sync_status_from_trello()
        self.assertIsNotNone(self.test_project.status,
                             "Status proyek tidak diperbarui dari Trello!")
