import React from 'react';
import { TamaguiProvider } from 'tamagui';
import tamaguiConfig from '../../../tamagui.config';
import { StatusBar } from 'expo-status-bar';
import { ErrorBoundary } from '../../shared/components/ErrorBoundary';
import RootNavigator from './navigation/RootNavigator';

export default function WorkerApp() {
  return (
    <TamaguiProvider config={tamaguiConfig} defaultTheme="light">
      <ErrorBoundary>
        <StatusBar style="dark" />
        <RootNavigator />
      </ErrorBoundary>
    </TamaguiProvider>
  );
}
