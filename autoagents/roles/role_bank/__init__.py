from .engineer import Engineer
from .predefined_roles import ProductManager, Architect, ProjectManager

ROLES_LIST = []
# [
# {
#     'name': 'ProductManager',
#     'description': 'A professional product manager, the goal is to design a concise, usable, and efficient product.',
#     'requirements': 'Can only be selected when the task involves Python code development',
# },
# {
#     'name': 'Architect',
#     'description': 'A professional architect; the goal is to design a SOTA PEP8-compliant python system; make the best use of good open source tools.',
#     'requirements': 'Can only be selected when the task involves Python code development',
# },
# {
#     'name': 'ProjectManager',
#     'description': 'A project manager for Python development; the goal is to break down tasks according to PRD/technical design, give a task list, and analyze task dependencies to start with the prerequisite modules.',
#     'requirements': 'Can only be selected when the task involves Python code development',
# },
# {
#     'name': 'Engineer',
#     'description': 'A professional engineer; the main goal is to write PEP8 compliant, elegant, modular, easy to read and maintain Python 3.9 code',
#     'requirements': "There is a dependency relationship between the Engineer, ProjectManager, and Architect. If an Engineer is required, both Project Manager and Architect must also be selected.",
# },
# ]

ROLES_MAPPING = {
    'ProductManager': ProductManager,
    'Architect': Architect,
    'ProjectManager': ProjectManager,
    'Engineer': Engineer,
}