import React, { Component } from 'react';
import { Redirect } from 'react-router-dom';
import { connect } from 'react-redux';
import { verify } from '../actions/auth';
import AlertContext from './AlertContext';

class Activate extends Component {
    constructor(props) {
        super(props);
        this.state = {
            verified: false
        };
        this.verifyAccount = this.verifyAccount.bind(this)
    }

    verifyAccount() {
        const { match } = this.props;
        const uid = match.params.uid;
        const token = match.params.token;

        this.props.verify(uid, token);
        this.setState({ verified: true });
    };
    static contextType = AlertContext;

    render() {
        const { verified } = this.state;

        if (verified) {
            this.context.setAlertMessage('Your account has been successfully created and verified! You can now login.')
            return <Redirect to='/' />;
        }

        return (
            <div className='container'>
                <div
                    className='d-flex flex-column justify-content-center align-items-center'
                    style={{ marginTop: '200px' }}
                >
                    <h1>Verify your Account:</h1>
                    <button
                        onClick={this.verifyAccount}
                        style={{ marginTop: '50px' }}
                        type='button'
                        className='btn btn-color'
                    >
                        Verify
                    </button>
                </div>
            </div>
        );
    }
}

export default connect(null, { verify })(Activate);
