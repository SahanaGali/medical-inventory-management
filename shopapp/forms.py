from django import forms
from django.contrib.auth.models import User
from shopapp.models import *
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
import re

class userForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "password"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['profile_picture','emp_id','first_name','last_name','mail_id','phone_number','address','salary']

    def clean_phone_number(self):
        phone_number = str(self.cleaned_data.get('phone_number'))
        if not re.fullmatch(r'\d{10}', phone_number):
            raise ValidationError("Phone number must be exactly 10 digits.")
        return int(phone_number)


class CustomerForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = Customer
        fields = ['first_name','last_name','username','password','address','city','state','pincode','phone_number','mail_id','profile_picture']

    def clean_phone_number(self):
        phone_number = str(self.cleaned_data.get('phone_number'))
        if not re.fullmatch(r'\d{10}', phone_number):
            raise ValidationError("Phone number must be exactly 10 digits.")
        return int(phone_number)


class CustomerForm1(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name','last_name','address','city','state','pincode','phone_number','mail_id','profile_picture']

    def clean_phone_number(self):
        phone_number = str(self.cleaned_data.get('phone_number'))
        if not re.fullmatch(r'\d{10}', phone_number):
            raise ValidationError("Phone number must be exactly 10 digits.")
        return int(phone_number)


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['medicine_name','medicine_code','dealer_name','price','stock','description']

class MedicineForm1(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['medicine_name','medicine_code','price','stock',]



class DealerForm(forms.ModelForm):
    class Meta:
        model = Dealer
        fields = ['dealer_name','company_name','address','phone','mail_id']
    
    def clean_phone(self):
        phone = str(self.cleaned_data.get('phone'))
        if not re.fullmatch(r'\d{10}', phone):
            raise ValidationError("Phone number must be exactly 10 digits.")
        return int(phone)

# class TabletForm(forms.ModelForm):
#     class Meta:
#         model = Tablet
#         fields = ['tablet_name','price']

SaleFormSet = modelformset_factory(
    SaleItem, fields=("medicine", "price", "quantity","discount","sub_total"), extra=1
)

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['customer','phone','confirmed','total']
        widgets = {
            'customer': forms.Select(attrs={'onchange': 'updateCustomerImage()'}),
        }
        
    def clean_phone(self):
        phone_number = str(self.cleaned_data.get('phone'))
        if not re.fullmatch(r'\d{10}', phone_number):
            raise ValidationError("Phone number must be exactly 10 digits.")
        return int(phone_number)

class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['medicine','price','quantity', 'discount','sub_total']

PurchaseFormSet = modelformset_factory(
    PurchaseItem, fields=("tablet_name", "price", "quantity",'total'), extra=1
)

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ["dealer", "phone",'total_amount']

    def clean_phone(self):
        phone_number = str(self.cleaned_data.get("phone"))
        if not re.fullmatch(r"\d{10}", phone_number):
            raise ValidationError("Phone number must be exactly 10 digits.")
        return int(phone_number)


class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseItem
        fields = ["tablet_name", "price", "quantity",'total']
        widgets = {
            "tablet_name": forms.Select(attrs={"id": "id_tablet_name"}),
        }

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price <= 0:
            raise ValidationError("Price must be a positive number.")
        return price

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity <= 0:
            raise ValidationError("Quantity must be a positive number.")
        return quantity   

class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = '__all__'
        
    def clean_phone_number(self):
        phone_number = str(self.cleaned_data.get('phone_number'))
        if not re.fullmatch(r'\d{10}', phone_number):
            raise ValidationError("Phone number must be exactly 10 digits.")
        return int(phone_number)

class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = '__all__'

class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder  
        fields = '__all__'                  