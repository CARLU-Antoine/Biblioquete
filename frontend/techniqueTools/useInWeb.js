import { Platform } from 'react-native';

const useIsWeb = () => Platform.OS === 'web';
export default useIsWeb;