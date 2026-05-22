import { useState } from 'react';
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp, NativeStackScreenProps } from '@react-navigation/native-stack';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Star } from 'lucide-react-native';
import { clientRatingsService } from '../../../shared/services/client-ratings.service';
import type { HomeStackParamList } from '../navigation/types';
import { ScreenHeader } from './components';
import { C, clientStyles } from './clientStyles';

type Navigation = NativeStackNavigationProp<HomeStackParamList>;
type RouteProps = NativeStackScreenProps<HomeStackParamList, 'RateRequirement'>['route'];

const STAR_COUNT = 5;

const RATING_LABELS: Record<number, string> = {
  1: 'Poor',
  2: 'Fair',
  3: 'Good',
  4: 'Very Good',
  5: 'Excellent',
};

export default function RateRequirementScreen() {
  const navigation = useNavigation<Navigation>();
  const route = useRoute<RouteProps>();
  const insets = useSafeAreaInsets();
  const { requirementId, category } = route.params;

  const [rating, setRating] = useState(0);
  const [comments, setComments] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submit = async () => {
    if (rating === 0) {
      Alert.alert('Select a rating', 'Please tap the stars to give a rating before submitting.');
      return;
    }

    setIsSubmitting(true);
    try {
      await clientRatingsService.submitRating({
        requirement_id: requirementId,
        rating,
        comments: comments.trim() || undefined,
      });
      Alert.alert('Rating submitted', 'Thank you for your feedback!', [
        { text: 'Done', onPress: () => navigation.goBack() },
      ]);
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        'Could not submit rating. Please try again.';
      Alert.alert('Error', msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <View style={[clientStyles.root, { paddingTop: insets.top }]}>
      <ScrollView contentContainerStyle={clientStyles.content} keyboardShouldPersistTaps="handled">
        <ScreenHeader
          title="Rate this job"
          subtitle={`How was your experience with ${category}?`}
          onBack={() => navigation.goBack()}
        />

        <View style={clientStyles.card}>
          <Text style={styles.label}>Your rating</Text>
          <View style={styles.stars}>
            {Array.from({ length: STAR_COUNT }, (_, i) => i + 1).map((star) => (
              <Pressable key={star} onPress={() => setRating(star)} hitSlop={8} style={styles.starBtn}>
                <Star
                  size={36}
                  color={star <= rating ? C.warningText : C.border}
                  fill={star <= rating ? C.warningText : 'transparent'}
                />
              </Pressable>
            ))}
          </View>
          {rating > 0 ? (
            <Text style={styles.ratingLabel}>{RATING_LABELS[rating]}</Text>
          ) : (
            <Text style={[styles.ratingLabel, { color: C.muted }]}>Tap to rate</Text>
          )}
        </View>

        <View style={clientStyles.card}>
          <Text style={styles.label}>Comments (optional)</Text>
          <TextInput
            style={styles.textArea}
            value={comments}
            onChangeText={setComments}
            placeholder="Tell us more about your experience…"
            placeholderTextColor={C.muted}
            multiline
            numberOfLines={4}
            textAlignVertical="top"
            maxLength={1000}
          />
          <Text style={styles.charCount}>{comments.length} / 1000</Text>
        </View>

        <Pressable
          style={[styles.submitBtn, (isSubmitting || rating === 0) && styles.submitBtnDisabled]}
          onPress={submit}
          disabled={isSubmitting || rating === 0}
        >
          {isSubmitting ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <Text style={styles.submitText}>Submit rating</Text>
          )}
        </Pressable>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: C.ink,
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  stars: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 4,
  },
  starBtn: {
    padding: 4,
  },
  ratingLabel: {
    textAlign: 'center',
    marginTop: 10,
    fontSize: 15,
    fontWeight: '600',
    color: C.warningText,
  },
  textArea: {
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 8,
    padding: 12,
    minHeight: 100,
    fontSize: 14,
    color: C.ink,
    backgroundColor: '#FAFAFA',
  },
  charCount: {
    marginTop: 6,
    fontSize: 11,
    color: C.muted,
    textAlign: 'right',
  },
  submitBtn: {
    backgroundColor: C.brand,
    borderRadius: 10,
    paddingVertical: 15,
    alignItems: 'center',
    marginTop: 8,
  },
  submitBtnDisabled: {
    opacity: 0.5,
  },
  submitText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
});
