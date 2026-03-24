from django.views.generic import TemplateView


class FrontendAppView(TemplateView):
	template_name = "common/index.html"
