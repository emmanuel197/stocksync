import {
    CART_DATA_REQUEST,
    CART_DATA_SUCCESS,
    CART_DATA_FAIL,
    COOKIE_CART_DATA_SUCCESS,
    COOKIE_CART_DATA_FAIL,
    UPDATE_ITEM_SUCCESS,
    UPDATE_ITEM_FAIL,
    ORDERED_ITEM_FAIL
    
} from '../actions/types';
import { createSelector } from 'reselect';

const initialState = {
    loading: false,
    totalItems: 0,
    totalCost: 0,
    itemList: [],
    shipping: false,
    error: null
};


const cartDataFromLocalStorage = JSON.parse(localStorage.getItem('cartData'));

export default function(state = cartDataFromLocalStorage || initialState, action) {
  const { type, payload } = action;

  switch(type) {
    case CART_DATA_REQUEST:
      return {
        ...state,
        loading: true
      }
    case CART_DATA_SUCCESS:
    case COOKIE_CART_DATA_SUCCESS:
      const cartData = {
        loading: false,
        totalItems: payload.total_items || payload.totalItems,
        totalCost: payload.total_cost || payload.totalCost,
        itemList: payload.items || payload.itemList,
        shipping: payload.shipping,
        error: null
      };
      localStorage.setItem('cartData', JSON.stringify(cartData));
      return cartData;
    case CART_DATA_FAIL:
    case COOKIE_CART_DATA_FAIL:
      const emptyCartData = {
        loading: false,
        totalItems: 0,
        totalCost: 0,
        itemList: [],
        shipping: false,
        error: payload
      };
      localStorage.setItem('cartData', JSON.stringify(emptyCartData));
      return emptyCartData;
    case UPDATE_ITEM_SUCCESS:
      const updatedItemIndex = state.itemList.findIndex(item => item.id === payload.updated_item.id)
      const updatedItemList = [...state.itemList];
      if (updatedItemIndex !== -1) {
        updatedItemList[updatedItemIndex] = payload.updated_item;
        const updatedCartData = {
          ...state,
          itemList: updatedItemList,
          totalItems: payload.total_items,
          totalCost: payload.total_cost
        };

        localStorage.setItem('cartData', JSON.stringify(updatedCartData));
        return updatedCartData;
      } else {
        updatedItemList[updatedItemList.length - 1] = payload.updated_item;
        const updatedCartData = {
          ...state,
          itemList: updatedItemList,
          totalItems: payload.total_items,
          totalCost: payload.total_cost
        }
        localStorage.setItem('cartData', JSON.stringify(updatedCartData));
        return updatedCartData;
      }
    case UPDATE_ITEM_FAIL:
        const updatedItemInd = state.itemList.findIndex(item => item.id === payload.item_id);
        const updateItemList = [...state.itemList];
        updateItemList.splice(updatedItemInd, 1)
        const updateCartData = {
            ...state,
            itemList: updateItemList,
            totalItems: payload.total_items,
            totalCost: payload.total_cost
          };
          localStorage.setItem('cartData', JSON.stringify(updateCartData));
          return updateCartData
    case ORDERED_ITEM_FAIL:
      const failedOrderCartData = {
        loading: false,
        totalItems: 0,
        totalCost: 0,
        itemList: [],
        shipping: false,
        error: payload
      };
      localStorage.setItem('cartData', JSON.stringify(failedOrderCartData));
      return failedOrderCartData;
    default:
      return state;
  }
};


const cartSelector = state => state.cart;

export const getItemQuantityById = createSelector(
  [cartSelector, (_, itemId) => itemId],
  (cart, itemId) => {
    const { itemList } = cart;
    const itemIds = itemList.map(item => item.id)
    let item = itemList.find(item => item.id == itemId);
    if (item) {
        return item.quantity;
    } else {
        const cartDataFromLocalStorage = JSON.parse(localStorage.getItem('cartData'));
        const itemFromLocalStorage = cartDataFromLocalStorage ? cartDataFromLocalStorage.itemList.find(item => item.id === itemId) : false;
        return itemFromLocalStorage ? itemFromLocalStorage.quantity : 0;
    }
  }
);
