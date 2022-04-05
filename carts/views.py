from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import Cart, CartItem
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist

# Create your views here.



def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

# Add products in cart items
def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variation = []

    # get product variation of current product to be added into cart
    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]
            print(key, value)
            try:
                variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                print(variation)
                product_variation.append(variation)
            except:
                pass
    
    # get the cart using cart_id present in the session
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request)) 
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id = _cart_id(request)
        )
    cart.save()
    
    # Checking whether cart item exits aleardy
    is_cart_item_exist = CartItem.objects.filter(product=product, cart=cart).exists()
    if is_cart_item_exist:
        cart_item = CartItem.objects.filter(product=product, cart=cart)
        ex_var_list =[]
        ci_id = []
        for item in cart_item:
            existing_variation = item.variation.all()
            
            # Converting query set to list
            ex_var_list.append(list(existing_variation))
            ci_id.append(item.id)

        print(ex_var_list)
        
           # Incease cart item quantity
        if product_variation in ex_var_list:
            # get cart item id
            index = ex_var_list.index(product_variation)
            itemid = ci_id[index]
            # get cart item
            ietm = CartItem.objects.get(product=product, id=itemid)
            item.quantity += 1
            item.save()

        # If  product & cart item exist and product variation does not exist 
        else:
            item = CartItem.objects.create(product = product, cart=cart, quantity = 1)
            if len(product_variation) > 0:
               item.variation.clear()  
               # This * will add all product variations               
               item.variation.add(*product_variation)          
            item.save()

    # Creating new cart item if cart item for product does not exist
    else:
        cart_item    = CartItem.objects.create (
            product  = product,
            quantity = 1,
            cart     = cart,
        )
        if len(product_variation) > 0:
            cart_item.variation.clear()
            cart_item.variation.add(*product_variation)
        cart_item.save()
    #return HttpResponse(cart_item.product)
    #exit()
    return redirect('cart')

# Remove products from cart_item
def remove_cart(request, product_id, cart_item_id):
    product   = get_object_or_404(Product, id=product_id)
    cart      = Cart.objects.get(cart_id=_cart_id(request))
    cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    try:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')

# Rmove cart item completely
def remove_cart_item(request, product_id, cart_item_id):
    product   = get_object_or_404(Product, id=product_id)
    cart      = Cart.objects.get(cart_id=_cart_id(request))
    cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax         = 0
        grand_total = 0
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        
        tax = total*0.18
        grand_total = total + tax

    except ObjectDoesNotExist:
        pass # Just ignore

    context = {
        'total' : total,
        'quanity' : quantity,
        'cart_items' : cart_items,
        'tax' : tax,
        'grand_total' : grand_total,
    }
    return render(request, 'store/cart.html', context)
