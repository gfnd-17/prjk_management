# -*- coding: utf-8 -*-
# from odoo import http


# class ProjectManagement(http.Controller):
#     @http.route('/project_management/project_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/project_management/project_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('project_management.listing', {
#             'root': '/project_management/project_management',
#             'objects': http.request.env['project_management.project_management'].search([]),
#         })

#     @http.route('/project_management/project_management/objects/<model("project_management.project_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('project_management.object', {
#             'object': obj
#         })
