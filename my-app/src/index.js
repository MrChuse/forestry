import React from 'react';
import ReactDOM from 'react-dom';
import arrowLeftSolid from './img/arrow-left-solid.svg';
import arrowRightSolid from './img/arrow-right-solid.svg';
import './index.css';

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

class CommandForm extends React.Component {
  constructor(props) {
    super(props);
    this.state = {value: '',
                  history: [],
                  history_pointer: -1};

    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.prev_text = this.prev_text.bind(this);
    this.next_text = this.next_text.bind(this);
  }

  handleChange(event) {
    this.setState({value: event.target.value});
  }

  async handleSubmit(event) {
    event.preventDefault();
    console.log('Sent command: ' + this.state.value);
    console.log(this.state.history.concat(this.state.value));
    this.setState({
      history: this.state.history.concat(this.state.value),
      history_pointer: this.state.history.length + 1
    });
	const response = await fetch(
		this.props.url,
		{
			method: this.props.method,
			body: this.state.value
		}
	);
	console.log('after fetch');
	const data = await response.text();
	if (data !== "Success") {
		throw new Error('not successful post');
	}
    this.setState({
        value: ''
    });
  }
  
  prev_text(event){
    const new_ptr = Math.max(this.state.history_pointer - 1, 0);
    if (new_ptr != 0 || this.state.history.length != 0){
        const new_value = this.state.history[new_ptr]
        this.setState({
            history_pointer: new_ptr,
            value: new_value
        });
    }
  }
  
  next_text(event){
      const new_ptr = Math.min(this.state.history_pointer + 1, this.state.history.length);
      if (new_ptr == this.state.history.length){
          this.setState({
              history_pointer: new_ptr,
              value: ''
          });
      }
      else {
          this.setState({
              history_pointer: new_ptr,
              value: this.state.history[new_ptr]
          });
      }
  }
  
  render() {
    return (
        <div className="console">
            <form className="consoleForm" onSubmit={this.handleSubmit}>
              
                <input type="text" autoFocus="autoFocus" value={this.state.value} onChange={this.handleChange} />
                <input type="submit"/>
              
            </form>
            <img className="arrowLeft" src={arrowLeftSolid} alt="Prev Command" onClick={this.prev_text}/>
            <img className="arrowRight" src={arrowRightSolid} alt="Prev Command" onClick={this.next_text}/>
        </div>
    );
  }
}

class FetchableText extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			value: ''
		}
	}
	
	async update_text() {
        fetch(this.props.url)
        .then(response => {
            if (response.ok){
                return response.json();
            }
        })
        .then(data => this.setState({ value: data['text'] }))
        .catch(reason => {
            console.log(reason);
            return Promise.reject()
        });
	}
	
	async componentDidMount() {
		while (true) {
			this.update_text();
			await sleep(this.props.sleep_time);
		}
	}
	
	render() {
		const l = this.state.value.split(/\r?\n/).map((el, index) => {
			return <li key={index}>{el}</li>
		})
		return <ul>{l}</ul>;
	}
}

class Game extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
		}
	}
    render() {
		return (
				<div>
					<FetchableText url="http://127.0.0.1:8081/out" sleep_time={100}/>
					<FetchableText url="http://127.0.0.1:8081/command_out" sleep_time={100}/>
					<CommandForm url="http://127.0.0.1:8081/command" method="post"/>
				</div>
			);
	}
}

// ========================================

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<Game />);
