from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from houseexpense.core.models import House
from django.utils import timezone


class HomeView(TemplateView):
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            if self.request.user.is_manager():
                context['house'] = House.objects.filter(manager=self.request.user).first()
            else:
                flats = self.request.user.flats_owned.all()
                context['flats'] = flats
                if flats.exists():
                    context['house'] = flats.first().house
        return context


