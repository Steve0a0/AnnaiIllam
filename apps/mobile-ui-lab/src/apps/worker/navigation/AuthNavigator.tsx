import { createNativeStackNavigator } from '@react-navigation/native-stack';
import BuildProfileScreen from '../screens/auth/BuildProfileScreen';
import ConsentScreen from '../screens/auth/ConsentScreen';
import WelcomeScreen from '../screens/auth/WelcomeScreen';
import LoginScreen from '../screens/auth/LoginScreen';
import ProfileSubmittedScreen from '../screens/auth/ProfileSubmittedScreen';
import VerifyIdentityScreen from '../screens/auth/VerifyIdentityScreen';
import VerifyOtpScreen from '../screens/auth/VerifyOtpScreen';
import type { WorkerAuthStackParamList } from './types';

const Stack = createNativeStackNavigator<WorkerAuthStackParamList>();

export default function AuthNavigator() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Welcome" component={WelcomeScreen} />
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="VerifyOtp" component={VerifyOtpScreen} />
      <Stack.Screen name="Consent" component={ConsentScreen} />
      <Stack.Screen name="VerifyIdentity" component={VerifyIdentityScreen} />
      <Stack.Screen name="BuildProfile" component={BuildProfileScreen} />
      <Stack.Screen name="ProfileSubmitted" component={ProfileSubmittedScreen} />
    </Stack.Navigator>
  );
}
