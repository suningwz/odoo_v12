# -*- coding: utf-8 -*-

# encoding: utf-8


from odoo import models, fields, api, _ 

class ProjectStatus(models.Model):
        _inherit = 'project.status'

        def nbr_prjs(self):
                for r in self:
                        r.nb_project = len(r.projects)

        projects = fields.One2many('project.project', 'project_status', string="Projects")
        nb_project = fields.Integer('Nbrs.',compute=nbr_prjs)
        grp_kanban = fields.Char('Nom kanban')
        color = fields.Integer('Color Index')


        def action_show_tasks(self):
                action = self.env.ref('project.action_view_task').read()[0]
                action['views'] = [
                        (self.env.ref('project.view_task_tree2').id, 'tree'),
                        (self.env.ref('project.view_task_kanban').id, 'kanban'),
                        (self.env.ref('project.view_task_form2').id, 'form'),
                ]
                action['context'] = {'group_by': ['project_id']}
                # action['context'] = {'group_by': ['name_group',]}
                action['domain'] = [('project_id', 'in', self.projects.ids)]
                return action

# class ProjectTask(models.Model):
#         _inherit = 'project.task'

#         @api.depends('project_id', 'project_id.user_id', 'project_id.date_start', 'project_id.date')
#         def compute_name_group(self):
#                 """project, responsable, date start, date end"""
#                 for r in self:
#                         project_id = r.project_id
#                         project = project_id and project_id.name[:34] or ''
#                         user = project_id and project_id.user_id and project_id.user_id.name[:34] or ''
#                         ds = project_id and project_id.date_start or ''
#                         de = project_id and project_id.date or ''
#                         project = project.ljust(35,'.')
#                         user = user.ljust(35,'.')
#                         de = str(de).ljust(35,'.')
#                         ds = str(ds).ljust(35,'.')
#                         r.name_group = '%s | %s | %s | %s'%(
#                                 project, user, ds, de)
#         name_group = fields.Char("Group", compute=compute_name_group, store=True) 
