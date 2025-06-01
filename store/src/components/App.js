import React, { Component } from "react";
import ReactDOM from "react-dom";
import NavBar from "./Navbar";
import Homepage from "./Homepage";
import { Provider } from "react-redux";
import store from "../store";
import AlertContext from './AlertContext';
export default class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      cart_total_updated: false,
      cartUpdated: false,
      alertMessage: null,
    };
    this.updatedToggler = this.updatedToggler.bind(this);
    this.cartUpdatedToggler = this.cartUpdatedToggler.bind(this);
  }
  updatedToggler() {
    this.setState((prevState) => {
      return {
        ...prevState,
        cart_total_updated: !prevState.cart_total_updated,
      };
    });
  }
  cartUpdatedToggler() {
    this.setState((prevState) => ({
      ...prevState,
      cartUpdated: !prevState.cartUpdated,
    }));
  }

  setAlertMessage = (message) => {
    this.setState({ alertMessage: message });
  }
  render() {
    return (
      <div>
        <AlertContext.Provider value={{ 
        alertMessage: this.state.alertMessage, 
        setAlertMessage: this.setAlertMessage 
      }}>
        <Homepage
          cart_total_updated={this.state.cart_total_updated}
          updatedToggler={this.updatedToggler}
          cartUpdatedToggler={() => {
            this.cartUpdatedToggler();
          }}
          cartUpdated={this.state.cartUpdated}
        />
        </AlertContext.Provider>
      </div>
    );
  }
}

const root = document.getElementById("app");
ReactDOM.render(
  <Provider store={store}>
    <App />
  </Provider>, root
);
