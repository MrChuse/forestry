import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

class NameForm extends React.Component {
  constructor(props) {
    super(props);
    this.state = {value: ''};

    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
  }

  handleChange(event) {
    this.setState({value: event.target.value});
  }

  async handleSubmit(event) {
    console.log('Отправленное имя: ' + this.state.value);
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
    event.preventDefault();
  }

  render() {
    return (
      <form onSubmit={this.handleSubmit}>
        <input type="text" autoFocus="autoFocus" value={this.state.value} onChange={this.handleChange} />
        <input type="submit" value="Отправить" />
      </form>
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
	
	async get_text() {
		fetch(this.props.url)
        .then(response => response.json())
        .then(data => this.setState({ value: data['text'] }));
	}
	
	async componentDidMount() {
		while (true) {
			this.get_text();
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
					<NameForm url="http://127.0.0.1:8081/command" method="post"/>
				</div>
			);
	}
}

// ========================================

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<Game />);
