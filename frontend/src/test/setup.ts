import { JSDOM } from 'jsdom';
const jsdom = new JSDOM('', {
  url: 'http://localhost/',
});
globalThis.window = jsdom.window;
globalThis.document = jsdom.window.document;
globalThis.Node = jsdom.window.Node;
globalThis.NodeList = jsdom.window.NodeList;
globalThis.HTMLCollection = jsdom.window.HTMLCollection;
afterEach(() => {
  jsdom.window.close();
});
import '@testing-library/jest-dom';
