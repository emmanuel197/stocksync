import React, { Component } from "react";
import { Redirect } from "react-router-dom";
import { connect } from "react-redux";
import { reset_password } from "../actions/auth";

class ResetPassword extends Component {
  constructor(props) {
    super(props);
    this.state = {
      requestSent: false,
      formData: {
        email: "",
      },
    };
    this.onChange = this.onChange.bind(this);
    this.onSubmit = this.onSubmit.bind(this);
  }

  onChange(e) {
    const { name, value } = e.target;
    this.setState({
      formData: {
        ...this.state.formData,
        [name]: value,
      },
    });
  }

  onSubmit(e) {
    e.preventDefault();

    const { email } = this.state.formData;
    this.props.reset_password(email);
    this.setState({ requestSent: true });
  }

  render() {
    const { requestSent, formData } = this.state;
    const { email } = formData;

    if (requestSent) {
      return <Redirect to="/" />;
    }

    return (
      <div className="container mt-5">
        <h1>Request Password Reset:</h1>
        <div className="d-flex justify-content-center align-items-center" style={{height: "70vh"}}>
        <form onSubmit={this.onSubmit}>
          <div id="reset-password-card" className="card text-center">
            <div className="card-body">
              <p className="card-text py-2">
                Enter your email address and we'll send you an email with
                instructions to reset your password.
              </p>
              <div className="form-outline mb-3 px-2">
                <input className='form-control'
                            type='email'
                            placeholder='Email'
                            name='email'
                            value={email}
                            onChange={this.onChange}
                            required />
                
              </div>
               <button id="register-submit-button" type='submit'>
                        Reset Password
                    </button>
              <div className="d-flex justify-content-between mt-4">
                <a className="" href="#">
                  Login
                </a>
                <a className="" href="#">
                  Register
                </a>
              </div>
            </div>
          </div>
        </form>
        </div>
      </div>
    );
  }
}

export default connect(null, { reset_password })(ResetPassword);
