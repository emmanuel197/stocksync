import json
from .models import *

def cookieCart(request):

	#Create empty cart for now for non-logged in user
	try:
		cart = json.loads(request.COOKIES['cart'])
		# print(cart)
	except:
		cart = {}
		print('CART:', cart)

	items = []
	order = {'get_cart_total':0, 'get_cart_items':0, 'shipping':False}
	cartItems = order['get_cart_items']

	for i in cart:
		# print(i)
		#We use try block to prevent items in cart that may have been removed from causing error
		try:	
			if(cart[i]['quantity']>0): #items with negative quantity = lot of freebies  
				cartItems += cart[i]['quantity']
				product = Product.objects.get(id=i)
				total = (product.price * cart[i]['quantity'])

				order['get_cart_total'] += total
				# print(order)
				order['get_cart_items'] += cart[i]['quantity']

				item = {
				'id': product.id,
				'product':product.name, 
				'price': product.price, 
				'image':product.image.url, 
				'quantity':cart[i]['quantity'],
				'total': total
				}
				items.append(item)

				if product.digital == False:
					order['shipping'] = True
				# cart_data = {'cartItems':cartItems ,'order':order, 'items':items}
		except:
			pass
			
	return { 'total_items': order['get_cart_items'],
            'total_cost': order['get_cart_total'],
            'items': items,
            'shipping': order['shipping']
                }


# def cartData(request):
# 	cookieData = cookieCart(request)
# 	cartItems = cookieData['cartItems']
# 	order = cookieData['order']
# 	items = cookieData['items']

# 	return {'cartItems':cartItems ,'order':order, 'items':items}