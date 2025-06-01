import React, { Component } from "react";
import CartPage from "./CartPage";
import ProductPage from "./ProductPage";
import CheckoutPage from "./CheckoutPage";
import RegisterPage from "./RegisterPage";
import LoginPage from "./LoginPage";
import Activate from "./Activate";
import ResetPassword from "./ResetPassword";
import ResetPasswordConfirm from "./ResetPasswordConfirm";
import Google from "./Google";
import { BrowserRouter, Switch, Route } from "react-router-dom";
import Product from "./Product";
import Layout from "../hocs/Layout";
import SearchComponent from "./SearchComponent";
import FilterComponent from "./Filter";
import { connect } from "react-redux";
import Footer from "./Footer";
import Hero from "./Hero";
import AboutPage from "./AboutPage";
import AlertContext from "./AlertContext";
import ProductCardLoader from "./ProductCardLoader";
class Homepage extends Component {
  constructor(props) {
    super(props);
    this.productsSection = React.createRef();
    this.renderHomePage = this.renderHomePage.bind(this);
    this.state = {
      query: null,
      searchClicked: false,
    };
    this.queryToggler = this.queryToggler.bind(this);
    this.scrollToProducts = this.scrollToProducts.bind(this);
    this.searchClickedToggler = this.searchClickedToggler.bind(this)
  }
  static contextType = AlertContext;

  queryToggler(query) {
    this.setState((prevstate) => {
      return { ...prevstate, query: query };
    });
  }
  searchClickedToggler() {
    this.setState((prevState) => {
      return { searchClicked: !prevState.searchClicked  }
    });
  }

  scrollToProducts = () => {
    this.productsSection.current.scrollIntoView({ behavior: "smooth" });
  };

  renderHomePage() {
    return (
      <div>
        <Hero scrollToProducts={this.scrollToProducts} />
        <div className="container mt-5">
          <div className="row">
            <div className="col-lg-4">
              <h2 className="mb-4">Filter</h2>
              <FilterComponent
              />
            </div>
            <div className="col-lg-8">
              <SearchComponent
                query={this.state.query}
                queryToggler={(query) => {
                  this.queryToggler(query);
                }}
                searchClicked={this.state.searchClicked}
                searchClickedToggler={this.searchClickedToggler}
              />
              {this.state.searchClicked ? (
                this.state.query ? (
                  this.props.products.length > 0 ? (
                    <h6>Results for "{this.state.query}" query:</h6>
                  ) : (
                    <h6>There are no results for "{this.state.query}" query</h6>
                  )
                ) : (
                  <h6>There are no results for "" query</h6>
                )
              ) : null}
              <div
                id="products-section"
                ref={this.productsSection}
                className="row justify-content-md-center"
              > 
                {this.props.loading && Array.from({ length: 6 }).map((_, index) => (
              <ProductCardLoader key={index} />))}
                {(this.props.products && !this.props.loading) &&
                  this.props.products.map((product) => (
                    <Product
                      key={product.id}
                      product={product}
                    />
                  ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
  render() {
    return (
      <BrowserRouter>
        <Layout/>
        <Switch>
          <Route exact path="/">
            {this.renderHomePage()}
          </Route>
          <Route
            path="/cart"
            render={(props) => (
              <CartPage
                {...props}
              />
            )}
          />
          <Route
            path="/product/:id"
            render={(props) => {
              return (
                <ProductPage
                  {...props}
                />
              );
            }}
          />
          <Route
            path="/checkout"
            render={(props) => <CheckoutPage {...props}/>}
          />
          <Route path="/register" component={RegisterPage} />
          <Route path="/about" component={AboutPage} />
          <Route
            path="/login"
            render={(props) => {
                return <LoginPage {...props} />;
            }}
          />
          <Route
            path="/activate/:uid/:token"
            render={(props) => {
              return <Activate {...props} />;
            }}
          />
          <Route exact path="/reset-password" component={ResetPassword} />
          <Route
            path="/password/reset/confirm/:uid/:token"
            render={(props) => {
              return <ResetPasswordConfirm {...props} />;
            }}
          />
          <Route exact path="/google" component={Google} />
        </Switch>
        <Footer />
      </BrowserRouter>
    );
  }
}

const mapStateToProps = (state) => ({
  isAuthenticated: state.auth.isAuthenticated,
  formErrors: state.auth.formErrors,
  products: state.products.products,
  loading: state.products.loading
});

export default connect(mapStateToProps, null)(Homepage);
