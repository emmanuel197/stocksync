import React, { Component } from "react";
import CheckoutProduct from "./CheckoutProduct";
import { connect } from "react-redux";
import { getCookie } from "../util";
import AlertContext from './AlertContext';
class CheckoutPage extends Component {
  constructor(props) {
    super(props);

    this.state = {
      userInfo: {
        first_name: "",
        last_name: "",
        email: "",
      },
      shippingInfo: {
        address: "",
        city: "",
        state: "",
        zipcode: "",
        country: "",
      },
      formButtonClicked: false,
      orderComplete: this.props.orderComplete,
    };

    this.handleChange = this.handleChange.bind(this);
    this.onFormButtonClick = this.onFormButtonClick.bind(this);
    this.processOrder = this.processOrder.bind(this);
    this.unAuthProcessOrder = this.unAuthProcessOrder.bind(this);
    this.renderPaypalButtons = this.renderPaypalButtons.bind(this);
  }


  static contextType = AlertContext;

  processOrder() {
    const jwtToken = localStorage.getItem("access");
    const requestOptions = {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `JWT ${jwtToken}`,
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify({
        total: this.props.totalCost,
        user_info: this.state.userInfo,
        shipping_info: this.state.shippingInfo,
      }),
    };
    fetch("/api/process-order/", requestOptions)
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        if (data.order_status) {
          // Redirect to the registration page
          this.context.setAlertMessage('You have successfully completed your purchase! Check your  email for a confirmation of your order details');
          localStorage.removeItem('cartData');
          
          this.props.history.push(data.redirect);
        } else {
          window.location.replace("/");
        }
      })
      .catch((error) => {
        console.error(error);
      });
  }
  unAuthProcessOrder() {
    const requestOptions = {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify({
        total: this.props.totalCost,
        user_info: this.state.userInfo,
        shipping_info: this.state.shippingInfo,
      }),
    };
    fetch("/api/unauth-process-order/", requestOptions)
      .then((response) => {
        return response.json();
      })
      .then(async (data) => {
        if (data.order_status) {
          // Redirect to the registration page
          document.cookie = "cart=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
          this.context.setAlertMessage('You have successfully completed your purchase! Check your  email for a confirmation of your order');
          
          this.props.history.push(data.redirect);
        } else {

          this.context.setAlertMessage('Your purchase was not completed successfully');
          window.location.replace("/");
        }
      })
      .catch((error) => {
        console.error(error);
      });
  }
  renderPaypalButtons() {
    // Render PayPal buttons here
    const total = `${this.props.totalCost}`;
    const processOrder = this.processOrder;
    const unAuthProcessOrder = this.unAuthProcessOrder;
    const isAuthenticated = this.props.isAuthenticated;

    paypal
      .Buttons({
        style: {
          color: "blue",
          shape: "rect",
        },
        // Call your server to set up the transaction
        createOrder: function (data, actions) { 
          return actions.order.create({
            purchase_units: [
              {
                amount: {
                  value: parseFloat(total).toFixed(2),
                },
              },
            ],
          });
        },

        // Call your server to finalize the transaction

        // Finalize the transaction
        onApprove: function (data, actions) {
          return actions.order.capture().then((details) => {
            // Show a success message to the buyer

            if (isAuthenticated) {
              processOrder();
            } else {
              unAuthProcessOrder();
            }
          });
        },
      })
      .render("#paypal-button-container");
  }

  handleChange(event) {
    const { name, value } = event.target;
    this.setState((prevState) => ({
      userInfo: {
        ...prevState.userInfo,
        [name]: value,
      },
      shippingInfo: {
        ...prevState.shippingInfo,
        [name]: value,
      },
    }));
  }
  onFormButtonClick() {
    this.setState({ formButtonClicked: true });
  }

  render() {
    if (this.state.formButtonClicked) {
      const script = document.createElement("script");
      script.src =
        "https://www.paypal.com/sdk/js?client-id=AXZcDTvdaIqs36jgbZNz8h_N_f8GYo8uhVamcgiwK0__pvP8ftifpCK94lVnve8uDfBTW3QSV1sS5PJB&currency=USD&disable-funding=credit";
      script.async = true;
      script.onload = () => {
        this.renderPaypalButtons();
      };
      document.body.appendChild(script);
    }
    const checkoutProducts = this.props.itemList.map((item) => (
      <CheckoutProduct
        name={item.product}
        image={item.image}
        quantity={item.quantity}
        total={item.total}
      />
    ));
    const { first_name, last_name, email } = this.state.userInfo;
    const { address, city, state, zipcode, country } = this.state.shippingInfo;
    return (
      <div className="container">
        <div className="row mt-5">
          <div className="col-lg-6">
            <div className="box-element" id="form-wrapper">
              <div>
                {!this.props.isAuthenticated && (
                  <div id="user-info">
                    <div className="form-field">
                      <input
                        required
                        className="form-control"
                        type="text"
                        name="first_name"
                        placeholder="FirstName.."
                        value={first_name}
                        onChange={this.handleChange}
                      />

                    </div>
                    <div className="form-field">
                      <input
                        required
                        className="form-control"
                        type="text"
                        name="last_name"
                        placeholder="LastName.."
                        value={last_name}
                        onChange={this.handleChange}
                      />
                      
                    </div>
                    <div className="form-field">
                      <input
                        required
                        className="form-control"
                        type="email"
                        name="email"
                        placeholder="Email.."
                        value={email}
                        onChange={this.handleChange}
                      />
                    </div>
                  </div>
                )}

                {this.props.shipping && (
                  <div id="shipping-info">
                    <hr />
                    <p>Shipping Information:</p>
                    <hr />
                    <div className="form-field">
                      <input
                        className="form-control"
                        type="text"
                        name="address"
                        placeholder="Address.."
                        value={address}
                        onChange={this.handleChange}
                      />
                    </div>
                    <div className="form-field">
                      <input
                        className="form-control"
                        type="text"
                        name="city"
                        placeholder="City.."
                        value={city}
                        onChange={this.handleChange}
                      />
                    </div>
                    <div className="form-field">
                      <input
                        className="form-control"
                        type="text"
                        name="state"
                        placeholder="State.."
                        value={state}
                        onChange={this.handleChange}
                      />
                    </div>
                    <div className="form-field">
                      <input
                        className="form-control"
                        type="text"
                        name="zipcode"
                        placeholder="Zip code.."
                        value={zipcode}
                        onChange={this.handleChange}
                      />
                    </div>
                    <div className="form-field">
                      <input
                        className="form-control"
                        type="text"
                        name="country"
                        placeholder="Country.."
                        value={country}
                        onChange={this.handleChange}
                      />
                    </div>
                  </div>
                )}
                <hr />
                {this.state.formButtonClicked == false && (
                  <button
                    
                    className="btn btn-color btn-block w-100"
                    onClick={() => this.onFormButtonClick()}
                  >
                    Continue
                  </button>
                )}
              </div>
            </div>
            <br />
            {this.state.formButtonClicked && (
              <div className="box-element" id="payment-info">
                <small>Paypal Options</small>
                <div id="paypal-button-container"></div>
              </div>
            )}
          </div>

          <div className="col-lg-6">
            <div className="box-element">
              <a className="btn btn-outline-dark" href="/cart">
                &#x2190; Back to Cart
              </a>
              <hr />
              <h3>Order Summary</h3>
              <hr />
              {checkoutProducts}
              <h5>Items: {this.props.totalItems}</h5>
              <h5>Total: ${parseFloat(this.props.totalCost).toFixed(2)}</h5>
            </div>
          </div>
        </div>
      </div>
    );
  }
}
const mapStateToProps = (state) => ({
  isAuthenticated: state.auth.isAuthenticated,
  itemList: state.cart.itemList,
  totalItems: state.cart.totalItems,
  totalCost: state.cart.totalCost,
  shipping: state.cart.shipping,
  
});

export default connect(mapStateToProps, null)(CheckoutPage);
