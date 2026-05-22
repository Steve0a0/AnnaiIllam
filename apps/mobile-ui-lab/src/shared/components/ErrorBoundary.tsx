import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  message: string;
}

/**
 * Top-level React error boundary. Catches unexpected render/lifecycle errors
 * that would otherwise crash the app with a blank screen.
 *
 * Place at the root of each app variant (ClientApp, WorkerApp) to ensure
 * every navigation tree is covered.
 */
export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, message: '' };
  }

  static getDerivedStateFromError(error: unknown): State {
    const message =
      error instanceof Error ? error.message : 'An unexpected error occurred.';
    return { hasError: true, message };
  }

  componentDidCatch(error: unknown, info: React.ErrorInfo) {
    // Log to console in all envs; swap for a crash-reporting SDK (Sentry etc.) later.
    console.error('[ErrorBoundary] Uncaught render error:', error, info.componentStack);
  }

  handleRetry = () => {
    this.setState({ hasError: false, message: '' });
  };

  render() {
    if (this.state.hasError) {
      return (
        <SafeAreaView style={styles.root}>
          <View style={styles.content}>
            <Text style={styles.title}>Something went wrong</Text>
            <Text style={styles.body}>{this.state.message}</Text>
            <Pressable
              style={({ pressed }) => [styles.button, pressed && styles.buttonPressed]}
              onPress={this.handleRetry}
              accessibilityLabel="Retry"
            >
              <Text style={styles.buttonText}>Try again</Text>
            </Pressable>
          </View>
        </SafeAreaView>
      );
    }
    return this.props.children;
  }
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#f8f6f0',
  },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
    gap: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#17211a',
    textAlign: 'center',
  },
  body: {
    fontSize: 14,
    color: '#687267',
    textAlign: 'center',
    lineHeight: 20,
  },
  button: {
    marginTop: 8,
    backgroundColor: '#203428',
    borderRadius: 12,
    paddingVertical: 13,
    paddingHorizontal: 32,
  },
  buttonPressed: {
    opacity: 0.75,
  },
  buttonText: {
    color: '#fffdf8',
    fontSize: 15,
    fontWeight: '600',
  },
});
