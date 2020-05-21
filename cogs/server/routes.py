"""Setup routes for the Connect My Pairs API server"""
from . import views


def setup_routes(app):
    """Setup the routes for the server"""
    app.router.add_get('/', views.index)
