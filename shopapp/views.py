from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.forms import modelformset_factory
from django.template.loader import render_to_string
from django.core.serializers.json import DjangoJSONEncoder
from weasyprint import HTML
from decimal import Decimal
from django.core.mail import send_mail

from django.conf import settings 
import json
import io
import imaplib
import email
import re
from email.policy import default

from .models import *
from .forms import *


def get_medicine_price(request):
    medicine_id = request.GET.get('medicine_id')
    # print(medicine_id)
    if medicine_id:
        medicine = Medicine.objects.get(id=medicine_id)
        # print(medicine.medicine_name)
        return JsonResponse({'price': medicine.price})
    return JsonResponse({'price': 0})

def get_customer_details(request):
    customer_id = request.GET.get('customer_id')
    print(customer_id)
    try:
        customer = Customer.objects.get(id=customer_id)
        image_url = customer.profile_picture.url if customer.profile_picture else None
        print(customer.user)
        print(customer.phone_number)
        print(customer.profile_picture)
        data = {
            'phone': customer.phone_number,
            'image_url': image_url,
        }
        return JsonResponse(data)
    except Customer.DoesNotExist:
        return JsonResponse({'error': 'Customer not found'}, status=404)


def get_dealer_phone(request):
    phone = request.GET.get('dealer_id')
    if phone:
        dealer = Dealer.objects.get(id=phone)
        return JsonResponse({'phone':dealer.phone})
    return JsonResponse({'phone':0})


# def get_customer_image(request, customer_id):
#     try:
#         customer = Customer.objects.get(id=customer_id)
#         image_url = customer.profile_picture.url if customer.profile_picture else None
#         return JsonResponse({'image_url': image_url})
#     except Customer.DoesNotExist:
#         return JsonResponse({})


def register(request):
    if request.method == "POST":
        form = userForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            username = user.username
            password = form.cleaned_data.get('password') 
            user.set_password(password)
            user.save()

            UserDetails.objects.create(user=user,role='Customer')
            
            Customer.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                mail_id=user.email,   
            )

            return redirect('login')
    else:
        form = userForm()
    return render(request, 'register.html', {'form': form})

def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                auth_login(request, user)
                rle = UserDetails.objects.get(user=user)
                # print(rle.role)
                if str(rle.role) == 'Customer':
                    return redirect('customer_dashboard')
                elif str(rle.role) == 'Employee':
                    return redirect('employee_dashboard')
                elif str(rle.role) == 'Admin':
                # else:
                    return redirect('admin_dashboard')
                
            else:
                return HttpResponse('User is not active')
        else:
            return HttpResponse('Please check your credentials')
    return render(request, "login.html", {})

@login_required(login_url='login')
def customer_dashboard(request):
    return render(request, 'customer_dashboard.html',{})

@login_required(login_url='login')
def employee_dashboard(request):
    return render(request,'employee_dashboard.html')

@login_required(login_url='login')
def admin_dashboard(request):
    name = UserDetails.objects.get(user=request.user)
    employee = Employee.objects.get(user=name.user)
    return render(request,'admin_dashboard.html',{'name':employee,'rol':name})

@login_required(login_url='login')
def admin_logout(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def add_employee(request):
    if request.method == 'POST':
        username = request.POST.get('user_name')
        form = EmployeeForm(request.POST,request.FILES)
        if form.is_valid():
            employee = form.save(commit=False)
            first_name = employee.first_name
            last_name = employee.last_name
            # role = employee.role
            email = employee.mail_id
            password = username[:4] + str(employee.phone_number)[-4:]
            # create user
            user = User.objects.create_user(
                username=username, email=email, password=password,first_name=first_name,last_name=last_name
            )

            employee.user = user
            employee.id = user.id
            employee.save()

            # create user details
            UserDetails.objects.create(user=user,role = 'Employee')

            return redirect("emp_management")
    else:
        form = EmployeeForm()
    
    return render(request,'add_employee.html',{'form':form})

def add_admin(request):
    if request.method == 'POST':
        username = request.POST.get('user_name')
        form = EmployeeForm(request.POST,request.FILES)
        if form.is_valid():
            employee = form.save(commit=False)
            first_name = employee.first_name
            last_name = employee.last_name
            # role = employee.role
            email = employee.mail_id
            password = username[:4] + str(employee.phone_number)[-4:]
            # create user
            user = User.objects.create_user(
                username=username, email=email, password=password,first_name=first_name,last_name=last_name
            )

            employee.user = user
            employee.id = user.id
            employee.save()

            # create user details
            UserDetails.objects.create(user=user,role = 'Admin')

            return redirect("login")
    else:
        form = EmployeeForm()
    
    return render(request,'add_admin.html',{'form':form})

def customer_management(request):
    cust = Customer.objects.all()
    return render(request,'customer_mang.html',{'cust':cust})   

# Add Customer 👇👇
@login_required(login_url='login')
def add_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST,request.FILES)
        if form.is_valid():
            customer = form.save(commit=False)
            user = User.objects.create_user(username=customer.username,password = customer.password,first_name=customer.first_name,last_name=customer.last_name,email=customer.mail_id)
            customer.user = user
            customer.role = 'Customer'
            customer.save()
            UserDetails.objects.create(user=user,role='Customer')
            return redirect('customer_management')  
    else:
        form = CustomerForm()
    return render(request, 'add_customer.html', {'form': form})

@login_required(login_url='login')
def emp_management(request):
    emp = Employee.objects.all()
    return render(request,'emp_management.html',{'emp':emp})    

@login_required(login_url='login')
def dealer_Management(request):
    d = Dealer.objects.all()
    return render(request,'dealer_mang.html',{'d':d})


@login_required(login_url='login')
def add_dealer1(request):
    if request.method == 'POST':
        d_form = DealerForm(request.POST)
        if d_form.is_valid():
            dealer = d_form.save()
            request.session['dealer_id'] = dealer.id  
            return redirect('dealer_management') 
    else:
        d_form = DealerForm()
    
    context = {
        'd_form': d_form,
    }
    return render(request, 'add_dealer1.html', context)

@login_required(login_url='login')
def edit_dealer(request, pk):
    dealer = get_object_or_404(Dealer, pk=pk)
    MedicineFormSet = modelformset_factory(Medicine, form=MedicineForm1, extra=0)
    
    if request.method == 'POST':
        form = DealerForm(request.POST, instance=dealer)
        formset = MedicineFormSet(request.POST, queryset=Medicine.objects.filter(dealer_name=dealer))
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('dealer_management')
    else:
        form = DealerForm(instance=dealer)
        formset = MedicineFormSet(queryset=Medicine.objects.filter(dealer_name=dealer))
    
    return render(request, 'edit_dealer.html', {'form': form, 'formset': formset, 'dealer': dealer})

def generate_pdf(context):
    html_string = render_to_string('pdf_template.html', context)
    html = HTML(string=html_string)
    result = io.BytesIO()
    html.write_pdf(target=result)
    result.seek(0)
    return result

def find_quantity(name):
    med = Medicine.objects.get(medicine_name=name)
    return med.stock

@login_required(login_url='login')
def new_sale(request):
    formset = SaleFormSet(queryset=SaleItem.objects.none())
    if request.method == 'POST':
        formset = SaleFormSet(request.POST)
        s_form = SaleForm(request.POST)
        if s_form.is_valid() and formset.is_valid():
            if request.GET.get('download'):
                # Generate the PDF
                form_data = s_form.cleaned_data
                print(form_data)
                formset_data = [form.cleaned_data for form in formset if form.cleaned_data]
                print(formset_data)
                context = {
                    'customer': form_data['customer'],
                    'phone': form_data['phone'],
                    'total':form_data['total'],
                    'items': formset_data
                }
                
                pdf_buffer = generate_pdf(context)
                return FileResponse(pdf_buffer, as_attachment=True, filename='invoice.pdf')
            else:
                sale = s_form.save()
                for form in formset:
                    item = form.save(commit=False)
                    name = item.medicine
                    quant = find_quantity(name.medicine_name)
                    if item.quantity > quant:
                        s = Sale.objects.get(id=sale.id)
                        s.delete()
                        return HttpResponse(f"Insufficient stock for {name}. Available: {quant}, Requested: {item.quantity}")
                        break
                    item.sale = sale
                    item.save()
                # sale.save()
                total = sale.total
                print('Sale Total',total)

                if int(total) > 4000:
                    sale.tax = 18
                    sale.save()
                elif int(total) >= 2000:
                    sale.tax = 12
                    sale.save()
                elif int(total) >=1000:
                    sale.tax = 5
                    sale.save()
                else:
                    sale.tax = 0
                    sale.save()
                return redirect('sale_mang')
    else:
        s_form = SaleForm()
    
    return render(request, 'new_sale.html', {'s_form': s_form, 'sale_formset': formset})

@login_required(login_url='login')
def edit_sale(request, pk):
    sale = get_object_or_404(Sale, id=pk)
    sale_items = SaleItem.objects.filter(sale_id=sale.id)
    SaleFormSet = modelformset_factory(SaleItem, fields=('medicine','price', 'quantity','discount','sub_total'), extra=0)

    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale)
        formset = SaleFormSet(request.POST, queryset=sale_items)
        
        if form.is_valid() and formset.is_valid():
            if request.GET.get('download'):
                # Generate the PDF

                form_data = form.cleaned_data
                print(form_data)
                formset_data = [form.cleaned_data for form in formset if form.cleaned_data]
                print(formset_data)
                context = {
                    'customer': form_data['customer'],
                    'phone': form_data['phone'],
                    'total':form_data['total'],
                    'items': formset_data
                }
                
                pdf_buffer = generate_pdf(context)
                return FileResponse(pdf_buffer, as_attachment=True, filename='invoice.pdf')
            else:
                form.save()
                formset.save()
                
                delivery, created = Delivery.objects.get_or_create(sale=sale, defaults={'status': 'pending'})

                if not created:
                    
                    delivery.status = 'updated'  
                    delivery.save()

                return redirect('sale_mang')
    else:
        form = SaleForm(instance=sale)
        formset = SaleFormSet(queryset=sale_items)

    return render(request, 'edit_sale.html', {'form': form, 'sale': sale, 'formset': formset, 'sale_items': sale_items})

def PurchaseView(request):
    tablets = Medicine.objects.all()
    tablet_prices = {medicine.medicine_name: float(medicine.price) for medicine in tablets}
    print(tablet_prices)

    formset = PurchaseFormSet(queryset=PurchaseItem.objects.none())

    if request.method == 'POST':
        formset = PurchaseFormSet(request.POST)
        form = PurchaseForm(request.POST)

        if formset.is_valid() and form.is_valid():
            purchase_instance = form.save()
            name = purchase_instance.dealer.dealer_name

            try:
                dealer = Dealer.objects.get(dealer_name=name)
            except Dealer.DoesNotExist:
                dealer = None

            for item_form in formset:
                item_instance = item_form.save(commit=False)
                item_instance.purchase = purchase_instance

                try:
                    medicine = Medicine.objects.get(dealer_name=dealer, medicine_name=item_instance.tablet_name.medicine_name)
                except Medicine.DoesNotExist:
                    original_medicine = Medicine.objects.get(id=item_instance.tablet_name.id)
                    medicine = Medicine.objects.create(
                        dealer_name=dealer,
                        medicine_name=original_medicine.medicine_name,
                        medicine_code=original_medicine.medicine_code,
                        price=item_instance.price,
                        stock=item_instance.quantity,
                        description=original_medicine.description
                    )
                
                item_instance.tablet_name = medicine
                item_instance.save()

            purchase_instance.save()
            return redirect('purchase_mang')

    else:
        formset = PurchaseFormSet(queryset=PurchaseItem.objects.none())
        form = PurchaseForm()

    return render(request, 'new_purchase.html', {
        'purchase_formset': formset,
        'form': form,
    })

    
@login_required(login_url='login')
def edit_purchase(request,pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    PurchaseFormSet = modelformset_factory(PurchaseItem, fields=('tablet_name', 'price','quantity','total'), extra=0)
    
    if request.method == 'POST':
        form = PurchaseForm(request.POST, instance=purchase)
        formset = PurchaseFormSet(request.POST, queryset=PurchaseItem.objects.filter(purchase_id=purchase.id))
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('purchase_mang')
    else:
        form = PurchaseForm(instance=purchase)
        formset = PurchaseFormSet(queryset=PurchaseItem.objects.filter(purchase_id=purchase.id))
    
    return render(request, 'edit_purchase.html', {'form': form, 'formset': formset, 'purchase': purchase})
    

@login_required(login_url='login')
def medicine_management(request):
    med = Medicine.objects.all()
    return render(request,'medicine_mang.html',{'med':med})

@login_required(login_url='login')
def add_medicine(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('medicine_management')
    else:
        form = MedicineForm()
    return render(request, 'add_medicine.html', {'form': form})

@login_required(login_url='login')
def medicine_list(request):
    medicines = Medicine.objects.all()
    return render(request, 'medicine_list.html', {'medicines': medicines})

@login_required(login_url='login')
def sale_management(request):
    s = Sale.objects.all().order_by('-id')
    return render(request,'sale_mang.html',{'s':s})  

@login_required(login_url='login')
def delete_sale(request,pk):
    res = Sale.objects.get(id=pk)
    res.delete()
    return redirect('sale_mang')

@login_required(login_url='login')
def purchase_management(request):
    purchases = Purchase.objects.all().order_by('-id')
    return render(request, 'purchase_mang.html', {'pur': purchases})

@login_required(login_url='login')
def delete_purchase(request,pk):
    res = Purchase.objects.get(id=pk)
    res.delete()
    return redirect('purchase_mang')
    

@login_required(login_url='login')
def delete_dealer(request,pk):
    res = Dealer.objects.get(id=pk)
    res.delete()
    return redirect('dealer_management')

@login_required(login_url='login')
def edit_medicine(request,pk):
    if request.method == 'POST':
        res = Medicine.objects.get(id=pk)
        form = MedicineForm(request.POST,instance=res)
        if form.is_valid():
            try:
                form.save()
                return redirect('medicine_management')
            except IntegrityError:
                form.add_error(None, 'There was an error saving the medicine. Please try again.')
    else:
        res = Medicine.objects.get(id=pk)
        form = MedicineForm(instance=res)
    return render(request,'edit_medicine.html',{'form':form,'res':res})

@login_required(login_url='login')
def delete_medicine(request,pk):
    res = Medicine.objects.get(id=pk)
    res.delete()
    return redirect('medicine_management')

@login_required(login_url='login')
def edit_employee(request,pk):
    if request.method == 'POST':
        res = Employee.objects.get(id=pk)
        form = EmployeeForm(request.POST,instance=res)
        if form.is_valid():
            form.save()
            return redirect('emp_management')

    else:
        res = Employee.objects.get(id=pk)
        form = EmployeeForm(instance=res)
    return render(request,'edit_employee.html',{'form':form,'res':res})

@login_required(login_url='login')
def delete_employee(request,pk):
    res = Employee.objects.get(id=pk)
    res.delete()
    return redirect('emp_management')

@login_required(login_url='login')
def edit_customer(request,pk):
    if request.method == 'POST':
        res = Customer.objects.get(id=pk)
        form = CustomerForm1(request.POST,request.FILES,instance=res)
        if form.is_valid():
            form.save()
            return redirect('customer_management')
    else:
        res = Customer.objects.get(id=pk)
        form = CustomerForm1(instance=res)
    return render(request,'edit_customer.html',{'form':form,'res':res})

@login_required(login_url='login')
def delete_customer(request,pk):
    res = Customer.objects.get(id=pk)
    res.delete()
    return redirect('customer_management')

@login_required(login_url='login')
def delivery_management(request):
    dlry = Delivery.objects.all().order_by('-id')
    return render(request,'delivery_mang.html',{'dlry':dlry})

def delivery_report(request,pk):
    dlry = Delivery.objects.get(id=pk)
    return render(request,'delivery_report.html',{'dlry':dlry})

def confirm(request):
    sales = Sale.objects.all()
    return render(request,'confirm.html',{'sales':sales})

def confirm_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        sale.status = True
        sale.save()
        return redirect('sale_mang')
    return render(request, 'confirm_sale.html', {'sale': sale})

def confirm_purchase(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if request.method == 'POST':
        purchase.status = True
        purchase.save()
        return redirect('purchase_mang')
    return render(request, 'confirm_purchase.html', {'purchase': purchase})

def confirm_delivery(request, pk):
    delivery = get_object_or_404(Delivery, pk=pk)
    if request.method == 'POST':
        delivery.status = 'DELIVERED'
        delivery.save()
        return redirect('delivery_mang')
    return render(request, 'change_delivery_status.html', {'delivery': delivery})

@require_POST
def change_status(request,pk):
    if request.method == 'POST':
        try:
            delivery = Delivery.objects.get(pk=pk)
            delivery.status = 'DELIVERED'
            delivery.save()
            return redirect('delivery_mang')
        except Delivery.DoesNotExist:
            print('delivery model doesnotexist')
    return render(redirect,'change_delivery_status.html',{})
    


@login_required(login_url='login')
def crm_management(request):
    crm = Lead.objects.all()
    return render(request,'crm_mang.html',{'crm':crm})

@login_required(login_url='login')
def view_lead(request):
    leads = Lead.objects.all()
    return render(request,'view_lead.html',{'leads':leads})

def confirm_lead(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        lead.status = True
        lead.save()
        return redirect('view_lead')
    return render(request, 'confirm_lead.html', {'lead': lead})
    
@login_required(login_url='login')
def view_opportunity(request):
    opportunities = Opportunity.objects.all()
    return render(request,'view_opportunity.html',{'opportunities':opportunities})

def confirm_opportunity(request, pk):
    oppo = get_object_or_404(Opportunity, pk=pk)
    if request.method == 'POST':
        oppo.status = True
        oppo.save()
        return redirect('view_opportunity')
    return render(request, 'confirm_opportunity.html', {'oppo': oppo})    

def confirm_sale_order(request,pk):
    sale = get_object_or_404(SalesOrder,pk=pk)
    if request.method == 'POST':
        sale.status = True
        sale.save()
        return redirect('view_sale_order')
    return render(request,'confirm_sale_order.html',{'sale':sale})

@login_required(login_url='login')
def view_sale_order(request):
    sale_order = SalesOrder.objects.all()
    return render(request,'view_sale_order.html',{'sale_order':sale_order})

def mail_configuration(request):
    if request.method == 'POST':
        mail = request.POST.get('email')
        pswrd = request.POST.get('password')
        fetch_and_store_email_data(mail, pswrd)
    
    return render(request, 'mail_configuration.html', {})

def extract_email_details(email_body):
    details = {}
    username_match = re.search(r"Username:\s*(.*)", email_body)
    first_name_match = re.search(r"First Name:\s*(.*)", email_body)
    last_name_match = re.search(r"Last Name:\s*(.*)", email_body)
    phone_match = re.search(r"Phone:\s*(.*)", email_body)
    email_match = re.search(r"Email:\s*(.*)", email_body)

    if username_match and first_name_match and last_name_match and phone_match and email_match:
        details['username'] = username_match.group(1).strip()
        details['first_name'] = first_name_match.group(1).strip()
        details['last_name'] = last_name_match.group(1).strip()
        details['phone'] = phone_match.group(1).strip()
        details['email'] = email_match.group(1).strip()
    else:
        return None

    tablets = re.findall(r"Tablet:\s*(.*?)\s*Quantity:\s*(.*?)\s*(?=Tablet|\Z)", email_body, re.DOTALL)
    parsed_tablets = []
    for t in tablets:
        tablet, quantity = t[0].strip(), t[1].strip()
        if not tablet or not quantity.isdigit():
            continue
        parsed_tablets.append({
            'tablet': tablet,
            'quantity': int(quantity),
        })
    details['tablets'] = parsed_tablets

    return details

def find_customer(username, first_name, last_name, phone, email):
    try:
        customer = Customer.objects.get(user__username=username)
    except Customer.DoesNotExist:
        user = User.objects.create_user(username=username, password=phone, first_name=first_name, last_name=last_name, email=email)
        customer = Customer.objects.create(user=user, first_name=first_name, last_name=last_name, phone_number=phone, mail_id=email)
        customer.role = 'Customer'
        customer.save()
        UserDetails.objects.create(user=user, role='Customer')
    return customer

def send_mail_to_customer(email, no_medicine):
    try:
        subject = 'Your Order Details'
        if no_medicine:
            message = "Hi, the following tablets are currently out of stock in our shop:\n\n"
            for item in no_medicine:
                if item:
                    message += f"Tablet: {item['Tablet']}, Requested Quantity: {item['Quantity']}, Available in Shop: {item['Available_in_shop']}\n"
            message += "\nThe remaining items are placed successfully."
        else:
            message = 'Hi, Your Med Plus+ Order has been placed successfully'
        
        email_from = settings.EMAIL_HOST_USER
        email_to = [email]
        
        send_mail(subject, message, email_from, email_to)
        print(f"Email sent to {email} with subject: '{subject}'")
        return True
    except Exception as e:
        print(f"Error sending email to {email}: {e}")
        return False

def find_tablet(name, quantity):
    try:
        tablet = Medicine.objects.filter(medicine_name=name).first()
        if tablet:
            print(f"Found tablet: {tablet.medicine_name}, Stock: {tablet.stock}")
            if quantity > tablet.stock:
                return None, {'Tablet': name, 'Quantity': quantity, 'Available_in_shop': tablet.stock}
            return tablet, None
        else:
            print(f"Tablet not found: {name}")
            return None, {'Tablet': name, 'Quantity': quantity, 'Available_in_shop': 0}
    except Medicine.DoesNotExist:
        print(f"Tablet not found: {name}")
        return None, {'Tablet': name, 'Quantity': quantity, 'Available_in_shop': 0}

def fetch_and_store_email_data(email_address, password):
    try:
        # Connect to the email server
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(email_address, password)
        mail.select('inbox')

        # Search for unseen emails
        status, data = mail.search(None, 'UNSEEN')
        email_ids = data[0].split()

        for email_id in email_ids:
            # Fetch the email
            status, data = mail.fetch(email_id, '(RFC822)')
            raw_email = data[0][1]

            # Parse the email content
            msg = email.message_from_bytes(raw_email, policy=default)
            email_body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        email_body = part.get_payload(decode=True).decode()
                        break
            else:
                email_body = msg.get_payload(decode=True).decode()

            # Extract details from the email body
            details = extract_email_details(email_body)
            if not details:
                print('No details extracted from email')
                continue

            print(f"Extracted details: {details}")

            # Find or create the customer
            customer = find_customer(details['username'], details['first_name'], details['last_name'], details['phone'], details['email'])

            # Create the lead
            lead = Lead.objects.create(
                name=customer,
                phone=details['phone'],
                email=details['email']
            )

            # Track out-of-stock medicines
            no_medicine = []

            # Create the lead tablets
            for tablet in details['tablets']:
                tab, out_of_stock_message = find_tablet(tablet['tablet'], tablet['quantity'])
                if tab:
                    LeadTablet.objects.create(
                        lead=lead,
                        tablet=tab,
                        quantity=tablet['quantity']
                    )
                else:
                    if out_of_stock_message:
                        no_medicine.append(out_of_stock_message)

            # Log no_medicine content for debugging
            print("no_medicine content:", no_medicine)

            # Send notification email if any medicines are out of stock
            try:
                send_mail_to_customer(details['email'], no_medicine)
            except Exception as e:
                print(f"Error sending Email: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        mail.logout()

    return redirect('crm_mang')