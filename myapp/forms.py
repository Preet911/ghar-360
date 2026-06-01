from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Property
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "mobile",
            "occupation",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "mobile": forms.TextInput(attrs={"class": "form-control"}),
            "occupation": forms.TextInput(attrs={"class": "form-control"}),
        }



class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            "title",
            "description",
            "rent",
            "looking_to",
            "property_type",
            "building",
            "city",
            "locality",
            "bhk",
            "built_up_area",
            "area_unit",
            "furnish_type",
            # New furnishing fields (booleans)
            "dining_table",
            "washing_machine",
            "cupboard",
            "sofa",
            "microwave",
            "stove",
            "fridge",
            "water_purifier",
            "gas_pipeline",
            "chimney",
            "modular_kitchen",
            "power_backup",
            "swimming_pool",
            "gym",
            "lift",
            "intercom",
            "garden",
            "sports",
            "kids_area",
            "CCTV",
            "gated_community",
            "club_house",
            "community_hall",
            "regular_water_supply",
            "security_guard",
            "visitor_parking",
            "maintenance_staff",
            "housekeeping",
            "parking",
            "visitor_parking",
            

            # New furnishing fields (integers)
            "fan",
            "light",
            "ac",
            "wardrobe",
            "tv",
            "bed",
            "geyser",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "rent": forms.NumberInput(attrs={"class": "form-control"}),

            "looking_to": forms.RadioSelect(),
            "property_type": forms.RadioSelect(),
            "furnish_type": forms.RadioSelect(),

            "building": forms.TextInput(attrs={"class": "form-control"}),

            # ✅ Plain text city field (with autocomplete handled in template)
            "city": forms.TextInput(attrs={
                "id": "city-input",
                "class": "form-control",
                "placeholder": "Start typing a city..."
            }),
            "locality": forms.TextInput(attrs={
                "id": "locality-input",
                "class": "form-control",
                "placeholder": "Start typing locality..."
            }),

            "bhk": forms.Select(attrs={"class": "form-select"}),
            "built_up_area": forms.NumberInput(attrs={"class": "form-control"}),
            "area_unit": forms.Select(attrs={"class": "form-select"}),
            
            # 👉 Styling for new fields
            "dining_table": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "washing_machine": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "cupboard": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "sofa": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "microwave": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "stove": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "fridge": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "water_purifier": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "gas_pipeline": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "chimney": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "modular_kitchen": forms.CheckboxInput(attrs={"class": "form-check-input"}),

            "fan": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "light": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "ac": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "wardrobe": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "tv": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "bed": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "geyser": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            
            "power_backup": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "swimming_pool": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "gym": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "lift": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "intercom": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "garden": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "sports": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "kids_area": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "CCTV": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "gated_community": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "club_house": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "community_hall": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "regular_water_supply": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "security_guard": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "visitor_parking": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "maintenance_staff": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "housekeeping": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "parking": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "visitor_parking":  forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SignUpForm(UserCreationForm):
    mobile = forms.CharField(max_length=15)
    occupation = forms.CharField(max_length=100, required=False)
    # aadhaar_image = forms.ImageField(required=False, help_text="Upload Aadhaar image (JPG/PNG).")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username","first_name","last_name", "email", "mobile", "occupation", "password1", "password2")
        # fields = ("username", "email", "mobile", "password1", "password2", "aadhaar_image")
        # widgets = {
        #     "aadhaar_image": forms.ClearableFileInput(),
        # }

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    pass

class AadhaarUploadForm(forms.Form):
    aadhaar_image = forms.ImageField(required=True, help_text="Upload Aadhaar image (JPG/PNG)")