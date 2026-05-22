import { SafeAreaProvider } from 'react-native-safe-area-context';
import ClientApp from './src/apps/client';
import WorkerApp from './src/apps/worker';

const variant = process.env.EXPO_PUBLIC_APP_VARIANT;

const AppRoot = variant === 'worker' ? WorkerApp : ClientApp;

export default function App() {
  return (
    <SafeAreaProvider>
      <AppRoot />
    </SafeAreaProvider>
  );
}
