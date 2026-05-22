import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Keyboard,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { getApiError } from '../../../../shared/lib/get-api-error';
import { authService } from '../../../../shared/services/auth.service';
import type { WorkerAuthStackParamList } from '../../navigation/types';
import { C, authStyles as styles } from './styles';

type Props = NativeStackScreenProps<WorkerAuthStackParamList, 'Login'>;

export default function LoginScreen({ navigation }: Props) {
  const [phone, setPhone] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isPending, setIsPending] = useState(false);
  const isPhoneValid = /^\d{10,15}$/.test(phone.trim());

  const handleSendCode = async () => {
    if (!isPhoneValid) {
      Alert.alert('Invalid number', 'Please enter a valid phone number.');
      return;
    }

    Keyboard.dismiss();
    setIsPending(true);
    try {
      const result = await authService.requestOtp({ phone: phone.trim(), role: 'worker' });
      navigation.navigate('VerifyOtp', { phone: phone.trim(), devOtp: result?.otp });
    } catch (err) {
      Alert.alert('Error', getApiError(err, 'Failed to send code. Please try again.'));
    } finally {
      setIsPending(false);
    }
  };

  return (
    <SafeAreaView style={styles.root} edges={['top', 'bottom']}>
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <View style={styles.page}>
          <Text style={styles.heading}>Log in</Text>
          <Text style={styles.subheading}>
            We will send a one-time code to verify it is you.
          </Text>

          <Text style={loginStyles.label}>Phone number</Text>
          <View style={[styles.inputShell, isFocused && styles.inputFocused]}>
            <Text style={styles.prefix}>+91</Text>
            <TextInput
              style={styles.input}
              placeholder="Your phone number"
              placeholderTextColor={C.muted}
              keyboardType="phone-pad"
              value={phone}
              onChangeText={(value) => setPhone(value.replace(/\D/g, ''))}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              returnKeyType="done"
              onSubmitEditing={handleSendCode}
            />
          </View>
          <Text style={loginStyles.hint}>
            We will send you a one-time code to verify it is you.
          </Text>

          <View style={styles.spacer} />

          <Pressable
            style={({ pressed }) => [
              styles.button,
              isPhoneValid && styles.buttonPrimary,
              (!isPhoneValid || isPending) && styles.buttonDisabled,
              pressed && isPhoneValid && styles.buttonPressed,
            ]}
            onPress={handleSendCode}
            disabled={!isPhoneValid || isPending}
          >
            {isPending ? (
              <ActivityIndicator size="small" color={C.btnText} />
            ) : (
              <Text style={[styles.buttonText, isPhoneValid && styles.buttonTextPrimary]}>
                Connect
              </Text>
            )}
          </Pressable>
          <Text style={styles.terms}>By continuing you agree to our Terms</Text>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

import { StyleSheet } from 'react-native';
const loginStyles = StyleSheet.create({
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: C.ink,
    marginBottom: 6,
    letterSpacing: 0.1,
  },
  hint: {
    fontSize: 12,
    color: C.muted,
    marginTop: 4,
    lineHeight: 18,
  },
});
