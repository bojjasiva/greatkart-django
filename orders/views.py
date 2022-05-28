from multiprocessing import context
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from carts.models import CartItem
from store.models import Product
from orders.forms import OrderForm
from .models import Order, OrderProduct, Payment
import datetime
import json
from django.core.mail import EmailMessage
from django.template.loader import render_to_string



def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])
    # Store transction data to payments model
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['paymentMethod'],
        amount_paid = order.order_total,
        status = body['status']
                     )
    payment.save()
    order.payment = payment
    order.is_ordered = True
    order.save()

    # Move cart items to OrderProduct model
    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()
        
        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variation.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variation.set(product_variation)
        orderproduct.save()

    # Reduce quantity of products in Products model
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Clear cart items
    CartItem.objects.filter(user=request.user).delete()

    # send order received email to customer
    mail_subject = 'MyKart! Thank you for your order.!'
    message = render_to_string('orders/order_received_email.html',{
                'user'   : request.user,
                'order'  : order,
            })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    # send order number and transaction id back to the sendData method via JsonResponse
    data = {
        'order_number' : order.order_number,
        'transID' : payment.payment_id,
    }

    return JsonResponse(data)

def placeOrder(request, total=0, quantity=0):
    current_usser = request.user

    cart_items = CartItem.objects.filter(user=current_usser)
    cart_count = cart_items.count()
    if cart_count <=0:
        return redirect('store')
    
    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = total*0.18
    grand_total = total + tax


    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():

        # Creating instance of Order model and saving billing data
            data                = Order()

            data.user           = current_usser
            data.first_name     = form.cleaned_data['first_name']
            data.last_name      = form.cleaned_data['last_name']
            data.mobile         = form.cleaned_data['mobile']
            data.email          = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country        = form.cleaned_data['country']
            data.state          = form.cleaned_data['state']
            data.city           = form.cleaned_data['city']
            data.pincode        = form.cleaned_data['pincode']
            data.order_total    = grand_total
            data.tax            = tax
            data.ip             = request.META.get('REMOTE_ADDR')
            data.save()
        
        # Generating order number
            year = int(datetime.date.today().strftime('%Y'))
            day  = int(datetime.date.today().strftime('%d'))
            month = int(datetime.date.today().strftime('%m'))

            d = datetime.date(year, month, day) 
            current_date = d.strftime("%d%m%Y")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

        # getting the object of Order model
            order = Order.objects.get(user=current_usser, is_ordered=False, order_number=order_number)
            context = {
                'order' : order,
                'cart_items' : cart_items,
                'total' : total,
                'tax' : tax,
                'grand_total' : grand_total,

            }
            return render(request, 'orders/payments.html', context)

    return redirect('checkout')


def orderComplete(request):

    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price
        context = {
            'order' : order,
            'ordered_products' : ordered_products,
            'subtotal' : subtotal
        }
        return render(request, 'orders/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')

            

