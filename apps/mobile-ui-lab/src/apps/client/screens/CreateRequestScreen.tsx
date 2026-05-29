import { useMemo, useRef, useState } from 'react';
import type { ComponentProps } from 'react';
import { ActivityIndicator, Alert, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { GooglePlacesAutocomplete } from 'react-native-google-places-autocomplete';
import type { GooglePlacesAutocompleteRef } from 'react-native-google-places-autocomplete';
import DateTimePicker, { type DateTimePickerEvent } from '@react-native-community/datetimepicker';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { ArrowLeft, ArrowRight, Calendar, Check, MapPin, Minus, Plus, Send } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { clientRequirementsService, type CreateRequirementPayload } from '../../../shared/services/client-requirements.service';
import type { ClientAppStackParamList } from '../navigation/types';
import { ScreenHeader } from './components';
import { C, clientStyles } from './clientStyles';

type Navigation = NativeStackNavigationProp<ClientAppStackParamList>;

const JOB_TYPES = [
  'General Labour',
  'Security',
  'Housekeeping',
  'Packing',
  'Loading / Unloading',
  'Machine Operator',
  'Technical Trainee',
  'Electrician',
  'Welder',
  'Forklift Operator',
  'Other',
];

const SKILLS = ['Packing', 'Loading', 'Machine operation', 'Forklift', 'Electrical', 'Welding', 'Cleaning', 'Security', 'Night shift', 'Supervisor'];
const STATES = ['Tamil Nadu', 'Karnataka', 'Andhra Pradesh', 'Kerala', 'Telangana'];
const CITIES = ['Chennai', 'Sriperumbudur', 'Oragadam', 'Coimbatore', 'Hosur', 'Bengaluru', 'Hyderabad'];
const DURATIONS = ['1', '3', '7', '15', '30', '60', '90'];
const SHIFT_OPTIONS = [
  'General: 09:00-18:00',
  'Morning: 06:00-14:00',
  'Evening: 14:00-22:00',
  'Night: 22:00-06:00',
  'Double shift',
  'Triple shift',
  'Custom',
];

type FormState = {
  category: string;
  subcategory: string;
  work_location: string;
  city: string;
  state: string;
  site_latitude: number | null;
  site_longitude: number | null;
  number_of_workers: string;
  skills: string[];
  start_date: string;
  duration_days: string;
  shift_details: string;
  custom_shift: string;
  food_required: boolean;
  accommodation_required: boolean;
  budget_amount: string;
  notes: string;
};

const initialForm: FormState = {
  category: '',
  subcategory: '',
  work_location: '',
  city: 'Chennai',
  state: 'Tamil Nadu',
  site_latitude: null,
  site_longitude: null,
  number_of_workers: '10',
  skills: [],
  start_date: toDateInput(addDays(new Date(), 1)),
  duration_days: '7',
  shift_details: 'General: 09:00-18:00',
  custom_shift: '',
  food_required: false,
  accommodation_required: false,
  budget_amount: '',
  notes: '',
};

export default function CreateRequestScreen() {
  const navigation = useNavigation<Navigation>();
  const insets = useSafeAreaInsets();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<FormState>(initialForm);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const stepError = useMemo(() => validateStep(step, form), [step, form]);
  const isLastStep = step === 3;

  const update = (key: keyof FormState, value: string | boolean | string[] | number | null) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const next = () => {
    if (stepError) {
      Alert.alert('Check details', stepError);
      return;
    }
    setStep((value) => Math.min(value + 1, 3));
  };

  const submit = async () => {
    const allError = [0, 1, 2, 3].map((index) => validateStep(index, form)).find(Boolean);
    if (allError) {
      Alert.alert('Check details', allError);
      return;
    }

    const shiftDetails = form.shift_details === 'Custom' ? form.custom_shift.trim() : form.shift_details;
    const payload: CreateRequirementPayload = {
      category: form.category.trim(),
      subcategory: form.subcategory.trim() || null,
      number_of_workers: Number(form.number_of_workers),
      work_location: form.work_location.trim(),
      city: form.city.trim(),
      state: form.state.trim(),
      site_latitude: form.site_latitude,
      site_longitude: form.site_longitude,
      geofence_radius_meters: form.site_latitude != null ? 2000 : null,
      start_date: form.start_date.trim(),
      duration_days: Number(form.duration_days),
      shift_details: shiftDetails,
      food_required: form.food_required,
      accommodation_required: form.accommodation_required,
      budget_amount: form.budget_amount.trim() ? Number(form.budget_amount) : null,
      notes: [form.skills.length ? `Skills: ${form.skills.join(', ')}` : '', form.notes.trim()]
        .filter(Boolean)
        .join('\n\n') || null,
    };

    setIsSubmitting(true);
    try {
      const result = await clientRequirementsService.create(payload);
      navigation.replace('RequestDetail', { requirementId: result.id });
    } catch {
      Alert.alert('Could not submit request', 'Please check the details and try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={[clientStyles.root, { paddingTop: insets.top }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={clientStyles.content} keyboardShouldPersistTaps="handled">
        <ScreenHeader title="Request workers" subtitle={`Step ${step + 1} of 4`} onBack={() => navigation.goBack()} />

        <View style={styles.progressTrack}>
          <View style={[styles.progressFill, { width: `${((step + 1) / 4) * 100}%` }]} />
        </View>

        <View style={clientStyles.card}>
          {step === 0 ? <StepJob form={form} update={update} /> : null}
          {step === 1 ? <StepWorkers form={form} update={update} /> : null}
          {step === 2 ? <StepShift form={form} update={update} /> : null}
          {step === 3 ? <StepReview form={form} /> : null}
        </View>

        <View style={styles.actions}>
          {step > 0 ? (
            <Pressable style={styles.secondaryButton} onPress={() => setStep((value) => Math.max(value - 1, 0))}>
              <ArrowLeft size={16} color={C.brand} />
              <Text style={clientStyles.ghostButtonText}>Back</Text>
            </Pressable>
          ) : <View />}

          <Pressable
            style={[clientStyles.primaryButton, styles.actionPrimary, isSubmitting && { opacity: 0.6 }]}
            onPress={isLastStep ? submit : next}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : isLastStep ? (
              <>
                <Send size={16} color="#FFFFFF" />
                <Text style={clientStyles.primaryButtonText}>Submit</Text>
              </>
            ) : (
              <>
                <Text style={clientStyles.primaryButtonText}>Next</Text>
                <ArrowRight size={16} color="#FFFFFF" />
              </>
            )}
          </Pressable>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function StepJob({ form, update }: StepProps) {
  const placesRef = useRef<GooglePlacesAutocompleteRef>(null);
  const mapsKey = process.env.EXPO_PUBLIC_GOOGLE_MAPS_API_KEY ?? '';

  return (
    <View style={[styles.formGap, { zIndex: 10 }]}>
      <Text style={styles.stepTitle}>Job type and location</Text>
      <ChipGroup label="Job type" options={JOB_TYPES} selected={form.category} onSelect={(v) => update('category', v)} />
      {form.category === 'Other' ? (
        <Field label="Custom job type" value={form.subcategory} onChangeText={(v) => update('subcategory', v)} placeholder="Enter job type" />
      ) : (
        <Field label="Subcategory" value={form.subcategory} onChangeText={(v) => update('subcategory', v)} placeholder="Optional" />
      )}
      <View style={{ zIndex: 10 }}>
        <Text style={clientStyles.fieldLabel}>Work location</Text>
        <GooglePlacesAutocomplete
          ref={placesRef}
          placeholder="Search factory / site address…"
          onPress={(data, details = null) => {
            const lat = details?.geometry?.location?.lat ?? null;
            const lng = details?.geometry?.location?.lng ?? null;
            update('work_location', details?.formatted_address ?? data.description);
            update('site_latitude', lat);
            update('site_longitude', lng);
            const comps = details?.address_components ?? [];
            const city = comps.find((c) => c.types.includes('locality'))?.long_name ?? '';
            const state = comps.find((c) => c.types.includes('administrative_area_level_1'))?.long_name ?? '';
            if (city) update('city', city);
            if (state) update('state', state);
          }}
          query={{ key: mapsKey, language: 'en', components: 'country:in' }}
          fetchDetails
          minLength={3}
          enablePoweredByContainer={false}
          keyboardShouldPersistTaps="handled"
          textInputProps={{
            placeholderTextColor: C.muted,
            onChangeText: (v: string) => {
              if (!v) {
                update('work_location', '');
                update('site_latitude', null);
                update('site_longitude', null);
              } else {
                update('work_location', v);
              }
            },
          }}
          styles={{
            container: { flex: 0 },
            textInput: {
              height: 44,
              borderWidth: 1,
              borderColor: C.border,
              borderRadius: 8,
              paddingHorizontal: 12,
              fontSize: 15,
              color: C.ink,
              backgroundColor: '#FFFFFF',
            },
            listView: {
              borderWidth: 1,
              borderColor: C.border,
              borderRadius: 8,
              backgroundColor: '#FFFFFF',
              marginTop: 2,
            },
            row: { paddingVertical: 10, paddingHorizontal: 12 },
            description: { fontSize: 14, color: C.ink },
          }}
        />
        {form.site_latitude != null ? (
          <View style={styles.coordRow}>
            <MapPin size={11} color={C.brand} />
            <Text style={styles.coordText}>
              {form.site_latitude.toFixed(5)}, {form.site_longitude?.toFixed(5)}
            </Text>
          </View>
        ) : null}
      </View>
      <Field label="City" value={form.city} onChangeText={(v) => update('city', v)} placeholder="City" />
      <Field label="State" value={form.state} onChangeText={(v) => update('state', v)} placeholder="State" />
    </View>
  );
}

function StepWorkers({ form, update }: StepProps) {
  const workerCount = Number(form.number_of_workers) || 1;
  return (
    <View style={styles.formGap}>
      <Text style={styles.stepTitle}>Headcount and skills</Text>
      <View>
        <Text style={clientStyles.fieldLabel}>Number of workers</Text>
        <View style={styles.stepper}>
          <Pressable style={styles.stepperButton} onPress={() => update('number_of_workers', String(Math.max(1, workerCount - 1)))}>
            <Minus size={16} color={C.brand} />
          </Pressable>
          <TextInput
            style={styles.stepperInput}
            value={form.number_of_workers}
            onChangeText={(v) => update('number_of_workers', onlyDigits(v))}
            keyboardType="number-pad"
          />
          <Pressable style={styles.stepperButton} onPress={() => update('number_of_workers', String(workerCount + 1))}>
            <Plus size={16} color={C.brand} />
          </Pressable>
        </View>
      </View>
      <MultiChipGroup
        label="Required skills"
        options={SKILLS}
        selected={form.skills}
        onToggle={(skill) => {
          update(
            'skills',
            form.skills.includes(skill)
              ? form.skills.filter((item) => item !== skill)
              : [...form.skills, skill],
          );
        }}
      />
      <Field label="Budget amount" value={form.budget_amount} onChangeText={(v) => update('budget_amount', onlyDigits(v))} placeholder="Optional" keyboardType="number-pad" />
    </View>
  );
}

function StepShift({ form, update }: StepProps) {
  return (
    <View style={styles.formGap}>
      <Text style={styles.stepTitle}>Shift and dates</Text>
      <DateQuickPick value={form.start_date} onChange={(v) => update('start_date', v)} />
      <DatePickerField value={form.start_date} onChange={(v) => update('start_date', v)} />
      <ChipGroup label="Duration" options={DURATIONS.map((item) => `${item} days`)} selected={`${form.duration_days} days`} onSelect={(v) => update('duration_days', v.split(' ')[0])} />
      <ChipGroup label="Shift timing" options={SHIFT_OPTIONS} selected={form.shift_details} onSelect={(v) => update('shift_details', v)} />
      {form.shift_details === 'Custom' ? (
        <Field label="Custom shift timing" value={form.custom_shift} onChangeText={(v) => update('custom_shift', v)} placeholder="Example: 07:30-16:30" />
      ) : null}
      <ToggleRow label="Food provided at site for workers" value={form.food_required} onPress={() => update('food_required', !form.food_required)} />
      <ToggleRow label="Accommodation provided for workers" value={form.accommodation_required} onPress={() => update('accommodation_required', !form.accommodation_required)} />
    </View>
  );
}

function StepReview({ form }: { form: FormState }) {
  const shift = form.shift_details === 'Custom' ? form.custom_shift : form.shift_details;
  return (
    <View style={styles.formGap}>
      <Text style={styles.stepTitle}>Review and submit</Text>
      <Review label="Job" value={`${form.category}${form.subcategory ? ` / ${form.subcategory}` : ''} - ${form.number_of_workers} workers`} />
      <Review label="Location" value={`${form.work_location}, ${form.city}, ${form.state}`} />
      <Review label="Skills" value={form.skills.length ? form.skills.join(', ') : 'Not specified'} />
      <Review label="Dates" value={`${form.start_date} - ${form.duration_days} days`} />
      <Review label="Shift" value={shift || 'Not specified'} />
      <Review label="Worker provisions" value={`${form.food_required ? 'Food provided at site' : 'Food not provided'} - ${form.accommodation_required ? 'Accommodation provided' : 'Accommodation not provided'}`} />
      <Field label="Notes" value={form.notes} onChangeText={() => undefined} placeholder="No notes" multiline editable={false} />
    </View>
  );
}

type StepProps = {
  form: FormState;
  update: (key: keyof FormState, value: string | boolean | string[] | number | null) => void;
};

function ChipGroup({
  label,
  options,
  selected,
  onSelect,
  compact,
}: {
  label: string;
  options: string[];
  selected: string;
  onSelect: (value: string) => void;
  compact?: boolean;
}) {
  return (
    <View>
      <Text style={clientStyles.fieldLabel}>{label}</Text>
      <View style={[styles.chipWrap, compact && styles.compactChipWrap]}>
        {options.map((option) => (
          <Pressable
            key={option}
            style={[styles.chip, selected === option && styles.chipSelected]}
            onPress={() => onSelect(option)}
          >
            <Text style={[styles.chipText, selected === option && styles.chipTextSelected]}>{option}</Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}

function MultiChipGroup({
  label,
  options,
  selected,
  onToggle,
}: {
  label: string;
  options: string[];
  selected: string[];
  onToggle: (value: string) => void;
}) {
  return (
    <View>
      <Text style={clientStyles.fieldLabel}>{label}</Text>
      <View style={styles.chipWrap}>
        {options.map((option) => {
          const isSelected = selected.includes(option);
          return (
            <Pressable
              key={option}
              style={[styles.chip, isSelected && styles.chipSelected]}
              onPress={() => onToggle(option)}
            >
              <Text style={[styles.chipText, isSelected && styles.chipTextSelected]}>{option}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

function DateQuickPick({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  const options = [
    { label: 'Tomorrow', value: toDateInput(addDays(new Date(), 1)) },
    { label: 'In 3 days', value: toDateInput(addDays(new Date(), 3)) },
    { label: 'Next week', value: toDateInput(addDays(new Date(), 7)) },
  ];
  return (
    <View style={styles.formGap}>
      <ChipGroup label="Quick date" options={options.map((item) => item.label)} selected={options.find((item) => item.value === value)?.label ?? ''} onSelect={(label) => onChange(options.find((item) => item.label === label)?.value ?? value)} />
    </View>
  );
}

function DatePickerField({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  const [showPicker, setShowPicker] = useState(false);
  const selectedDate = parseDateInput(value);

  const handleChange = (_event: DateTimePickerEvent, date?: Date) => {
    if (Platform.OS !== 'ios') {
      setShowPicker(false);
    }
    if (date) {
      onChange(toDateInput(date));
    }
  };

  if (Platform.OS === 'web') {
    return (
      <Field
        label="Start date"
        value={value}
        onChangeText={(text) => onChange(formatDateInput(text))}
        placeholder="YYYY-MM-DD"
        keyboardType="number-pad"
        maxLength={10}
      />
    );
  }

  return (
    <View>
      <Text style={clientStyles.fieldLabel}>Start date</Text>
      <Pressable style={styles.dateButton} onPress={() => setShowPicker(true)}>
        <View>
          <Text style={styles.dateButtonValue}>{formatDateForDisplay(value)}</Text>
          <Text style={styles.dateButtonHint}>{value}</Text>
        </View>
        <Calendar size={18} color={C.brand} />
      </Pressable>
      {showPicker ? (
        <DateTimePicker
          value={selectedDate}
          mode="date"
          display={Platform.OS === 'ios' ? 'inline' : 'default'}
          minimumDate={startOfToday()}
          onChange={handleChange}
        />
      ) : null}
    </View>
  );
}

function Field({
  label,
  compact,
  multiline,
  ...props
}: {
  label: string;
  compact?: boolean;
  multiline?: boolean;
} & ComponentProps<typeof TextInput>) {
  return (
    <View style={compact ? { flex: 1 } : undefined}>
      <Text style={clientStyles.fieldLabel}>{label}</Text>
      <TextInput
        style={[clientStyles.input, multiline && clientStyles.textArea]}
        placeholderTextColor={C.muted}
        multiline={multiline}
        {...props}
      />
    </View>
  );
}

function ToggleRow({ label, value, onPress }: { label: string; value: boolean; onPress: () => void }) {
  return (
    <Pressable style={styles.toggleRow} onPress={onPress}>
      <Text style={styles.toggleLabel}>{label}</Text>
      <View style={[styles.checkbox, value && styles.checkboxOn]}>
        {value ? <Check size={14} color="#FFFFFF" /> : null}
      </View>
    </Pressable>
  );
}

function Review({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.reviewRow}>
      <Text style={styles.reviewLabel}>{label}</Text>
      <Text style={styles.reviewValue}>{value}</Text>
    </View>
  );
}

function validateStep(step: number, form: FormState) {
  if (step === 0) {
    if (form.category.trim().length < 2) return 'Choose the job type.';
    if (form.category === 'Other' && form.subcategory.trim().length < 2) return 'Enter the custom job type.';
    if (form.work_location.trim().length < 3) return 'Enter the work location.';
    if (form.city.trim().length < 2 || form.state.trim().length < 2) return 'Choose city and state.';
  }
  if (step === 1) {
    if (Number(form.number_of_workers) < 1) return 'Enter the number of workers needed.';
  }
  if (step === 2) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(form.start_date.trim())) return 'Enter start date as YYYY-MM-DD.';
    if (new Date(form.start_date) < startOfToday()) return 'Start date cannot be in the past.';
    if (Number(form.duration_days) < 1) return 'Choose duration in days.';
    if (form.shift_details === 'Custom' && form.custom_shift.trim().length < 5) return 'Enter the custom shift timing.';
  }
  return null;
}

function onlyDigits(value: string) {
  return value.replace(/\D/g, '');
}

function formatDateInput(value: string) {
  const digits = onlyDigits(value).slice(0, 8);
  const year = digits.slice(0, 4);
  const month = digits.slice(4, 6);
  const day = digits.slice(6, 8);

  if (digits.length <= 4) return year;
  if (digits.length <= 6) return `${year}-${month}`;
  return `${year}-${month}-${day}`;
}

function addDays(date: Date, days: number) {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

function toDateInput(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function parseDateInput(value: string) {
  const [year, month, day] = value.split('-').map(Number);
  if (!year || !month || !day) return startOfToday();

  const parsed = new Date(year, month - 1, day);
  return Number.isNaN(parsed.getTime()) ? startOfToday() : parsed;
}

function formatDateForDisplay(value: string) {
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).format(parseDateInput(value));
}

function startOfToday() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return today;
}

const styles = StyleSheet.create({
  progressTrack: {
    height: 3,
    backgroundColor: C.border,
    borderRadius: 999,
    overflow: 'hidden',
  },
  progressFill: {
    height: 3,
    backgroundColor: C.brand,
  },
  formGap: {
    gap: 14,
  },
  stepTitle: {
    color: C.ink,
    fontSize: 16,
    lineHeight: 22,
    fontWeight: '600',
  },
  chipWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  compactChipWrap: {
    gap: 6,
  },
  chip: {
    minHeight: 36,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: C.surface,
    paddingHorizontal: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  chipSelected: {
    borderColor: C.brand,
    backgroundColor: C.brand,
  },
  chipText: {
    color: C.body,
    fontSize: 13,
    fontWeight: '600',
  },
  chipTextSelected: {
    color: '#FFFFFF',
  },
  stepper: {
    minHeight: 52,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: C.surface,
    flexDirection: 'row',
    alignItems: 'center',
    overflow: 'hidden',
  },
  stepperButton: {
    width: 52,
    height: 52,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: C.brandSoft,
  },
  stepperInput: {
    flex: 1,
    textAlign: 'center',
    color: C.ink,
    fontSize: 18,
    fontWeight: '700',
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
  },
  actionPrimary: {
    minWidth: 132,
  },
  secondaryButton: {
    minHeight: 44,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
  },
  toggleRow: {
    minHeight: 52,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: C.surfaceAlt,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  dateButton: {
    minHeight: 54,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: C.surface,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  dateButtonValue: {
    color: C.ink,
    fontSize: 15,
    fontWeight: '700',
  },
  dateButtonHint: {
    color: C.muted,
    fontSize: 12,
    marginTop: 2,
  },
  toggleLabel: {
    color: C.ink,
    fontSize: 14,
    fontWeight: '600',
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: C.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxOn: {
    borderColor: C.brand,
    backgroundColor: C.brand,
  },
  reviewRow: {
    borderBottomWidth: 1,
    borderBottomColor: C.border,
    paddingBottom: 12,
  },
  reviewLabel: {
    color: C.muted,
    fontSize: 11,
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  reviewValue: {
    color: C.ink,
    fontSize: 14,
    lineHeight: 21,
    fontWeight: '600',
  },
  coordRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 4,
  },
  coordText: {
    color: C.brand,
    fontSize: 11,
    fontWeight: '500',
  },
});
