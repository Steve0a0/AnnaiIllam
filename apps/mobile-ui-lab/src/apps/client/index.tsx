import { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { ErrorBoundary } from '../../shared/components/ErrorBoundary';
import RootNavigator from './navigation/RootNavigator';

export default function ClientApp() {
  const [isDark, setIsDark] = useState(false);

  return (
    <ErrorBoundary>
      <StatusBar style={isDark ? 'light' : 'dark'} />
      <RootNavigator isDark={isDark} onToggleDark={() => setIsDark(d => !d)} />
    </ErrorBoundary>
  );
}
