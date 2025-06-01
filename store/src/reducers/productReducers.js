import {
    PRODUCTS_DATA_REQUEST,
    PRODUCTS_DATA_SUCCESS,
    PRODUCTS_DATA_FAIL,
    PRODUCT_DETAIL_REQUEST,
    PRODUCT_DETAIL_SUCCESS,
    PRODUCT_DETAIL_FAIL,
    PRODUCTS_FILTERED_REQUEST,
    PRODUCTS_FILTERED_SUCCESS,
    PRODUCTS_FILTERED_FAIL,
    RESET_PRODUCTS_SUCCESS,
    RESET_PRODUCTS_FAIL,
    SEARCH_PRODUCTS_REQUEST,
    SEARCH_PRODUCTS_SUCCESS,
    SEARCH_PRODUCTS_FAIL
} from '../actions/types';

const initialState = {
    loading: false,
    products: [],
    product: [],
    error: null
  };

const productsDataFromLocalStorage = JSON.parse(localStorage.getItem('productsData'));

export default function(state = productsDataFromLocalStorage || initialState, action) {
  const { type, payload } = action;

  switch(type) {
    case PRODUCTS_DATA_REQUEST:
    case PRODUCT_DETAIL_REQUEST:
    case PRODUCTS_FILTERED_REQUEST:
    case SEARCH_PRODUCTS_REQUEST:
      return {
        ...state,
        loading: true
      };
    case PRODUCTS_DATA_SUCCESS:
    case RESET_PRODUCTS_SUCCESS:
      const productsData = {
        ...state,
        loading: false,
        products: payload,
        error: null
      };
      localStorage.setItem('productsData', JSON.stringify(productsData));
      return productsData;
    case PRODUCTS_DATA_FAIL:
      const emptyProductsData = {
        ...state,
        loading: false,
        products: [],
        error: payload
      };
      localStorage.setItem('productsData', JSON.stringify(emptyProductsData));
      return emptyProductsData;
    case PRODUCT_DETAIL_SUCCESS:
        return {
            ...state,
            loading: false,
            product: payload,// Update original products with filtered results
            error: null
        };
    case PRODUCTS_FILTERED_SUCCESS:
    case SEARCH_PRODUCTS_SUCCESS:    
        return {
            ...state,
            loading: false,
            products: payload,// Update original products with filtered results
            error: null
        };
    case PRODUCT_DETAIL_FAIL:
    case PRODUCTS_FILTERED_FAIL:
    case SEARCH_PRODUCTS_FAIL: 
        return {
            ...state, 
            loading: false,
            error: payload
        }
    default:
      return state;
  }
};


