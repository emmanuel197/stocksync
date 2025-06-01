import React, { Component } from 'react';
import { Redirect } from 'react-router-dom';
import { connect } from 'react-redux';
import { reset_password_confirm } from '../actions/auth';

class ResetPasswordConfirm extends Component {
    constructor(props) {
        super(props);
        this.state = {
            requestSent: false,
            formData: {
                new_password: '',
                re_new_password: ''
            }
        };
        this.onChange = this.onChange.bind(this)
        this.onSubmit = this.onSubmit.bind(this)
    }

    onChange(e) {
        const { name, value } = e.target;
        this.setState((prevState) => ({
            formData: { ...prevState.formData, [name]: value }
        }));
    };

    onSubmit(e) {
        e.preventDefault();

        const { match, reset_password_confirm } = this.props;
        const { uid, token } = match.params;
        const { new_password, re_new_password } = this.state.formData;

        reset_password_confirm(uid, token, new_password, re_new_password);
        this.setState({ requestSent: true });
    };

    render() {
        const { requestSent, formData } = this.state;

        if (requestSent) {
            return <Redirect to='/' />;
        }

        return (
            <div className='container mt-5'>
                <form onSubmit={this.onSubmit}>
                    <div className='form-group'>
                        <input
                            className='form-control'
                            type='password'
                            placeholder='New Password'
                            name='new_password'
                            value={formData.new_password}
                            onChange={this.onChange}
                            minLength='6'
                            required
                        />
                    </div>
                    <div className='form-group'>
                        <input
                            className='form-control'
                            type='password'
                            placeholder='Confirm New Password'
                            name='re_new_password'
                            value={formData.re_new_password}
                            onChange={this.onChange}
                            minLength='6'
                            required
                        />
                    </div>
                    <button className='btn btn-primary' type='submit'>
                        Reset Password
                    </button>
                </form>
            </div>
        );
    }
}

export default connect(null, { reset_password_confirm })(ResetPasswordConfirm);
