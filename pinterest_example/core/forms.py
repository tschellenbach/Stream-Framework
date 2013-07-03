from core.models import Follow, Pin
from django import forms
from pinterest_example.core.pin_feedly import feedly


class PinForm(forms.ModelForm):

    class Meta:
        model = Pin
    
    def save(self, *args, **kwargs):
        pin = forms.ModelForm.save(self, *args, **kwargs)
        feedly.add_pin(pin)
        return pin


class FollowForm(forms.Form):
    user = forms.IntegerField()
    target = forms.IntegerField()

    def save(self):
        user = self.cleaned_data['user']
        target = self.cleaned_data['target']
        follow = Follow.objects.create(user_id=user, target_id=target)
        feedly.follow(follow)
        return follow
