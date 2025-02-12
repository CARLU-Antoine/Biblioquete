import {LogBox} from "react-native";
LogBox.ignoreLogs([
  "exported from 'deprecated-react-native-prop-types'.",
  "Method has been deprecated.",
  "Each child in a list should have a unique",
  "Encountered two children with the same key"
])
LogBox.ignoreAllLogs(true);
import { StyleSheet, Text, View } from 'react-native';
import MainPage from './screens/MainPage';
console.warn = () => {}; //Empêche les warn dans la console
export default function App() {
  return (
    MainPage()
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
