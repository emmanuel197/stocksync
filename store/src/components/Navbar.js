import React, { Component } from "react";
import cartIcon from "../../static/images/cart.png";
import { logout } from "../actions/auth";
import { connect } from "react-redux";
import kuandohWearLogo from "../../static/images/KuandorWear-logo4.png";
import AlertContext from './AlertContext';
class NavBar extends Component {
  constructor(props) {
    super(props);
    this.state = {
      totalItems: 0,
      orderComplete: this.props.orderComplete,
      cartUpdated: this.props.cartUpdated,
    };
    this.logOutHandler = this.logOutHandler.bind(this);
  }

 

  logOutHandler() {
    this.props.logout();
    this.props.history.push("/");
  }

  static contextType = AlertContext;
  
  render() {
    const firstName = this.props.user ? this.props.user.first_name : "Guest";
    const capitalizedFirstName = firstName.charAt(0).toUpperCase() + firstName.slice(1).toLowerCase();
    const { alertMessage, setAlertMessage } = this.context;
    console.log(`${this.props.user && this.props.user.last_login}`)
    return (
      <div>
        <nav className="store-nav">
      <div className="wrapper">
        <div className="logo"><a href="/"><img src={kuandohWearLogo}/></a></div>
        <input type="radio" name="slider" id="menu-btn"/>
        <input type="radio" name="slider" id="close-btn"/>
        <ul className="nav-links">
          <label for="close-btn" className="btn close-btn"><i class="fas fa-times"></i></label>
          <li><a href="/">Store</a></li>
          <li><a href="/about">About</a></li>
          {this.props.isAuthenticated ? (
              <li><a
                href="/"
                onClick={this.logOutHandler}
              >
                Logout
              </a></li>
            ) : (
              <li><a href="/login">Login</a></li>
            )}
          <li>
            <a href="/cart" id="cart-link">
                <img id="cart-icon" src={cartIcon}/>
                <span id="cart-total" className="badge rounded-circle text-center">{this.props.totalItems}</span>
                </a>
          </li>
        </ul>
        <label for="menu-btn" class="btn menu-btn"><i class="fas fa-bars"></i></label>
      </div>
        </nav>
        {alertMessage && (
          <div className="alert btn-color alert-dismissible fade show mb-0" role="alert">
          {alertMessage} {this.props.user && <span>Welcome Back, {capitalizedFirstName}</span>}
          <button type="button" className="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
      )}
    </div>
    );
  }
}

const mapStateToProps = (state) => ({
  isAuthenticated: state.auth.isAuthenticated,
  user: state.auth.user,
  totalItems: state.cart.totalItems
});

export default connect(mapStateToProps, { logout })(NavBar);
