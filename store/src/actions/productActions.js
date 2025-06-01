import axios from "axios";
import { getCookie } from "../util";
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

  } from "./types";


export const fetchProductsData = () => async (dispatch) => {
    try {
      dispatch({ type: PRODUCTS_DATA_REQUEST })
      const response = await axios.get("/api/products", {
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"), // Assuming getCookie function is defined elsewhere
        },
      });
      dispatch({ type: PRODUCTS_DATA_SUCCESS, payload: response.data });
    } catch (error) {
      dispatch({ type: PRODUCTS_DATA_FAIL, payload: error.message });
    }
    
  };

export const fetchProductDetail = (productId) => async (dispatch, getState) => {
try {
    const productList = getState().products.products;
    if (!productList || productList.length === 0) {
    // Fetch products from local storage if the productList is empty in the store
    const productsDataFromLocalStorage = JSON.parse(localStorage.getItem('productsData'));
    productList = productsDataFromLocalStorage ? productsDataFromLocalStorage.products : [];
    }
    const product = productList.find(product => product.id == productId);

    if (product) {
    dispatch({ type: PRODUCT_DETAIL_SUCCESS, payload: product });
    } else {
    throw new Error("Product not found");
    }
} catch (error) {
    dispatch({ type: PRODUCT_DETAIL_FAIL, payload: error.message });
}
};


export const fetchFilteredData = (minPrice, maxPrice, digital) => async (dispatch) => {

const queryParams = `min_price=${minPrice}&max_price=${maxPrice}&digital=${digital}`;

try {
    dispatch({ type: PRODUCTS_FILTERED_REQUEST });
    const response = await axios.get(`/api/products/filter/?${queryParams}`, {
    headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
    },
    });
    const data = response.data;
    dispatch({ type: PRODUCTS_FILTERED_SUCCESS, payload: data });
} catch (error) {
    console.error("Error fetching filtered data:", error);
    dispatch({ type: PRODUCTS_DATA_FAIL, payload: error.message });
}
};

export const resetProducts = () => {
try {
    const productsDataFromLocalStorage = JSON.parse(localStorage.getItem('productsData'));
    return {
    type: RESET_PRODUCTS_SUCCESS,
    payload: productsDataFromLocalStorage.products // Assuming productsDataFromLocalStorage has the structure { products: [] }
    }
} catch {
    return {
        type: RESET_PRODUCTS_FAIL
    }
}

}

export const searchProducts = (query) => async (dispatch) => {
    try {
      dispatch({ type: SEARCH_PRODUCTS_REQUEST })
      const response = await axios.get(`/api/search/?q=${query}`);
      // Dispatch action with search results
      dispatch({ type: SEARCH_PRODUCTS_SUCCESS, payload: response.data });
    } catch (error) {
      // Dispatch action for error handling
      dispatch({ type: SEARCH_PRODUCTS_FAIL, payload: error.message });
    }
  };