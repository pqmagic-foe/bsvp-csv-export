import React, { Component } from "react";
import styled, { createGlobalStyle } from "styled-components";
import Header from "./Header";
import Exporters from "./Exporters";
import Settings from "./Settings";
import { get } from "./api";

export default class App extends Component {
  constructor(props) {
    super(props);
    this.state = { manufacturers: null, selectAll: false, showSettings: false, buildInfo: null };
  }

  componentDidMount() {
    get("/manufacturers").then(manufacturers =>
      this.setState({
        manufacturers: manufacturers.reduce(
          (selectedManufacturers, manufacturer) => ({
            ...selectedManufacturers,
            [manufacturer]: true
          }),
          {}
        )
      })
    );
    get("/build-info").then(info => {
      this.setState({ buildInfo: info });
    });
  }

  render() {
    const { showSettings, manufacturers, selectAll, buildInfo } = this.state;
    return (
      <div className="App">
        <GlobalStyle />
        <Header showSettings={this.toggleSettings.bind(this)} />
        <Exporters manufacturers={manufacturers} />
        {manufacturers && (
          <Settings
            open={showSettings}
            close={this.toggleSettings.bind(this)}
            manufacturers={manufacturers}
            selectAll={selectAll}
            toggleManufacturer={this.toggleManufacturer.bind(this)}
            toggleAll={this.toggleAll.bind(this)}
          />
        )}
        {buildInfo && buildInfo.hash !== "unknown" && (
          <Footer>
            # {buildInfo.hash}{buildInfo.timestamp && ` · ${new Date(buildInfo.timestamp).toISOString().slice(0, 10)}`}
          </Footer>
        )}
      </div>
    );
  }

  toggleSettings() {
    const { showSettings } = this.state;
    this.setState({ showSettings: !showSettings });
  }

  toggleManufacturer(manufacturer) {
    const { manufacturers } = this.state;
    this.setState(
      {
        manufacturers: {
          ...manufacturers,
          [manufacturer]: !manufacturers[manufacturer]
        }
      },
      this.updateSelectAll
    );
  }

  updateSelectAll() {
    const { selectAll, manufacturers } = this.state;
    const firstSelection = manufacturers[Object.keys(manufacturers)[0]];
    const allSame = Object.keys(manufacturers).reduce(
      (previousSame, manufacturer) =>
        previousSame && manufacturers[manufacturer] === firstSelection,
      true
    );
    if (allSame && firstSelection === selectAll) {
      this.setState({ selectAll: !selectAll });
    }
  }

  toggleAll() {
    const { manufacturers, selectAll } = this.state;
    const toggledManufacturers = Object.keys(manufacturers).reduce(
      (reducedManufacturers, manufacturer) => ({
        ...reducedManufacturers,
        [manufacturer]: selectAll
      }),
      {}
    );
    this.setState({
      manufacturers: toggledManufacturers,
      selectAll: !selectAll
    });
  }
}

const Footer = styled.div`
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: #e0e0e0;
  color: #757575;
  font-size: 13px;
  text-align: center;
  padding: 6px 0;
`;

const GlobalStyle = createGlobalStyle`
  @font-face {
    font-family: "Roboto";
    src: url(./fonts/Roboto.ttf) format("truetype");
  }

  body {
    margin: 0;
    padding: 0;
    color: #141414;
    background-color: #fafafa;
    font-family: "Roboto", "Helvetica Neue", sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  code {
    font-family: source-code-pro, Menlo, Monaco, Consolas, "Courier New",
      monospace;
  }
`;
