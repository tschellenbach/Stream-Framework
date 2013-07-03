from core.models import Follow, Pin
from django import forms


class PinForm(forms.ModelForm):

    class Meta:
        model = Pin


class FollowForm(forms.Form):
    user = forms.IntegerField()
    target = forms.IntegerField()

    def save(self):
        user = self.cleaned_data['user']
        target = self.cleaned_data['target']
        follow = Follow.objects.create(user_id=user, target_id=target)
        return follow
