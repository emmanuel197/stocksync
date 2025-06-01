import {
  CART_DATA_REQUEST,
  CART_DATA_SUCCESS,
  CART_DATA_FAIL,
  COOKIE_CART_DATA_SUCCESS,
  COOKIE_CART_DATA_FAIL,
  ORDERED_ITEM_FAIL,
  UPDATE_ITEM_SUCCESS,
  UPDATE_ITEM_FAIL
} from "./types";
import axios from "axios";
import { getCookie } from "../util";

export const fetchCartData = () => async (dispatch) => {
  try {
    dispatch({ type: CART_DATA_REQUEST });

    const config = {
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
        Authorization: `JWT ${localStorage.getItem("access")}`,
      },
    };

    const res = await axios.get("/api/cart-data", config);

    dispatch({
      type: CART_DATA_SUCCESS,
      payload: res.data,
    });
  } catch (err) {
    dispatch({
      type: CART_DATA_FAIL,
    });
  }
};

// Initialize cart if it's not present in cookies
// let cart = JSON.parse(getCookie("cart"));
// if (cart === undefined) {
//   cart = {};
//   document.cookie = "cart=" + JSON.stringify(cart) + ";domain=;path=/";
// }


let cart = JSON.parse(getCookie("cart"));
if (cart === null) {
    cart = {};
    document.cookie = "cart=" + JSON.stringify(cart) + ";domain=;path=/";
} 

export const fetchCookieCart = () => async (dispatch) => {

  try {
    const items = [];
    let totalItems = 0;
    let totalCost = 0;
    let shipping = false;

    for (const productId in cart) {
      try {
        if (cart[productId].quantity > 0) {
          totalItems += cart[productId].quantity;

        const productsDataFromLocalStorage = JSON.parse(localStorage.getItem('productsData'));
        const productList = productsDataFromLocalStorage ? productsDataFromLocalStorage.products : [];
        const product = productList.find(product => product.id == productId);

          const total = product.price * cart[productId].quantity;
          totalCost += total;

          const item = {
            id: product.id,
            product: product.name,
            price: product.price,
            image: product.image,
            quantity: cart[productId].quantity,
            total: total,
          };

          items.push(item);

          if (!product.digital) {
            shipping = true;
          }
        }
      } catch (error) {
        console.error("Error processing cart item:", error);
      }
      
    }
    dispatch({
        type: COOKIE_CART_DATA_SUCCESS,
        payload: {
          totalItems: totalItems,
          totalCost: totalCost,
          itemList: items,
          shipping: shipping,
        }
      });
  } catch (error) {
    console.error("Error fetching cookie cart:", error);
    dispatch({
      type: COOKIE_CART_DATA_FAIL,
      error: error.message,
    });
  }
};

export const addOrRemoveCookieItem = (action, product_id) => async dispatch => {
    try {
        
      if (action === 'add') {
        if (cart[product_id] == undefined) {
          cart[product_id] = { 'quantity': 1 };
        //   console.log(cart[product_id])
        } else {
          cart[product_id]['quantity']++;
        }
      } else if (action == 'remove') {
        cart[product_id]['quantity']--;
        if (cart[product_id]['quantity'] <= 0) {
          delete cart[product_id];
        }
      }
      console.log(cart)
      // Update the cookie with the modified cart data
      document.cookie = 'cart=' + JSON.stringify(cart) + ';domain=;path=/';
  
      // Dispatch a success action or fetch updated cart data
      dispatch(fetchCookieCart());
    } catch (error) {
      console.error('Error adding or removing item:', error);
      dispatch({
        type: COOKIE_CART_DATA_FAIL,
        error: error.message
      });
    }
  };

export const handleOrderedItem = (product_id) => async (dispatch, getState) => {
    try {
        const jwtToken = localStorage.getItem('access');
        const config = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie("csrftoken"),
                'Authorization': `JWT ${jwtToken}`,
            }
        };
        const body = JSON.stringify({ "product_id": product_id });
        const res = await axios.post('/api/create-order/', body, config);

        // Optionally, you can update the state directly here without waiting for fetchCartData

        dispatch({
            type: UPDATE_ITEM_SUCCESS,
            payload: res.data
        });
    } catch (error) {
        console.error('Axios Error:', error);
        dispatch({
            type: ORDERED_ITEM_FAIL,
            error: error.message
        });
        // Optionally, you can dispatch CART_DATA_FAIL here if needed
    }
};

export const addOrRemoveItemHandler = (action, product_id) => async (dispatch, getState) => {
    
      const jwtToken = localStorage.getItem('access');
      const config = {
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
          'Authorization': `JWT ${jwtToken}`
        }
      };
  
      const response = await axios.post("/api/update-cart/", {
        action,
        product_id
      }, config);
  
      if (response.data.message === 'Cart updated successfully') {
        // Handle success
        dispatch({
            type: UPDATE_ITEM_SUCCESS,
            payload: response.data
        });
    } else if (response.data.error === 'Item does not exist') {
        // Handle not found error
        dispatch({
            type: UPDATE_ITEM_FAIL,
            payload: response.data
        })
      }
    } 
  ;
