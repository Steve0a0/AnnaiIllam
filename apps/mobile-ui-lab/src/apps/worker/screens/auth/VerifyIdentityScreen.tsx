import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as ImagePicker from 'expo-image-picker';
import * as DocumentPicker from 'expo-document-picker';
import Svg, { Path, Rect } from 'react-native-svg';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { getApiError } from '../../../../shared/lib/get-api-error';
import { authStorage } from '../../../../shared/lib/auth-storage';
import { workerOnboardingService } from '../../../../shared/services/worker-onboarding.service';
import { useAuthStore } from '../../../../shared/store/auth.store';
import type { WorkerAuthStackParamList } from '../../navigation/types';
import { C, authStyles as baseStyles } from './styles';

type Props = NativeStackScreenProps<WorkerAuthStackParamList, 'VerifyIdentity'>;

type UploadedFile = {
  uri: string;
  name: string;
  mimeType: string;
  fileSize?: number;
  type: 'id' | 'selfie';
};

function UploadIcon({ size = 24, color = C.brand }: { size?: number; color?: string }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <Path d="M12 16V8M12 8L9 11M12 8L15 11" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
      <Rect x="3" y="18" width="18" height="2" rx="1" fill={color} opacity={0.25} />
      <Path d="M3 18H21" stroke={color} strokeWidth={2} strokeLinecap="round" />
    </Svg>
  );
}

function FileRow({ file, onRemove }: { file: UploadedFile; onRemove: () => void }) {
  return (
    <View style={local.fileRow}>
      {file.uri.match(/\.(jpg|jpeg|png|gif|webp)$/i) ? (
        <Image source={{ uri: file.uri }} style={local.fileThumb} />
      ) : (
        <View style={local.fileThumbPlaceholder}>
          <Text style={local.fileThumbText}>📄</Text>
        </View>
      )}
      <Text style={local.fileName} numberOfLines={1}>{file.name}</Text>
      <Pressable onPress={onRemove} hitSlop={8}>
        <Text style={local.fileRemove}>✕</Text>
      </Pressable>
    </View>
  );
}

export default function VerifyIdentityScreen({ navigation }: Props) {
  const { setOnboardingStep } = useAuthStore();
  const [uploads, setUploads] = useState<UploadedFile[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const addFile = (uri: string, name: string, mimeType: string, type: 'id' | 'selfie', fileSize?: number) => {
    setUploads((prev) => [...prev.filter((f) => f.type !== type), { uri, name, mimeType, type, fileSize }]);
  };

  const pickImage = async (type: 'id' | 'selfie') => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Please allow access to your photo library.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      allowsMultipleSelection: false,
      quality: 0.85,
    });
    if (result.canceled) return;
    const asset = result.assets[0];
    addFile(asset.uri, asset.fileName ?? asset.uri.split('/').pop() ?? 'image.jpg', asset.mimeType ?? 'image/jpeg', type, asset.fileSize);
  };

  const pickDocument = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      type: ['image/*', 'application/pdf'],
      copyToCacheDirectory: true,
    });
    if (result.canceled) return;
    const asset = result.assets[0];
    addFile(asset.uri, asset.name, asset.mimeType ?? 'application/pdf', 'id', asset.size);
  };

  const pickId = () => {
    Alert.alert(
      'Upload govt ID',
      'Choose how you want to upload your document',
      [
        { text: 'Photo / Image', onPress: () => pickImage('id') },
        { text: 'Document (PDF)', onPress: () => pickDocument() },
        { text: 'Cancel', style: 'cancel' },
      ],
    );
  };

  const pick = async (type: 'selfie') => pickImage(type);

  const takeSelfie = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Please allow camera access to take a selfie.');
      return;
    }
    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ['images'],
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.85,
    });
    if (result.canceled) return;
    const asset = result.assets[0];
    addFile(asset.uri, asset.fileName ?? 'selfie.jpg', asset.mimeType ?? 'image/jpeg', 'selfie', asset.fileSize);
  };

  const pickSelfie = () => {
    Alert.alert(
      'Selfie',
      'Choose how you want to add your photo',
      [
        { text: 'Take a selfie', onPress: takeSelfie },
        { text: 'Choose from library', onPress: () => pickImage('selfie') },
        { text: 'Cancel', style: 'cancel' },
      ],
    );
  };

  const remove = (type: 'id' | 'selfie') => {
    setUploads((prev) => prev.filter((f) => f.type !== type));
  };

  const idFile = uploads.find((f) => f.type === 'id');
  const selfieFile = uploads.find((f) => f.type === 'selfie');
  const canSubmit = !!idFile && !!selfieFile;

  const handleNext = async () => {
    if (!idFile || !selfieFile) return;
    setIsSubmitting(true);
    try {
      const [idSize, selfieSize] = await Promise.all([
        idFile.fileSize ?? workerOnboardingService.getLocalFileSize(idFile.uri),
        selfieFile.fileSize ?? workerOnboardingService.getLocalFileSize(selfieFile.uri),
      ]);
      // Get size-bound presigned upload URLs from backend.
      const [idUpload, selfieUpload] = await Promise.all([
        workerOnboardingService.getUploadUrl('govt_id', idFile.mimeType, idSize),
        workerOnboardingService.getUploadUrl('selfie', selfieFile.mimeType, selfieSize),
      ]);

      let idKey: string;
      let selfieKey: string;

      if (idUpload.dev_mode || !idUpload.upload_url) {
        // Local dev: upload to backend filesystem storage, not S3.
        [idKey, selfieKey] = await Promise.all([
          workerOnboardingService.uploadLocalDocument('govt_id', idFile.uri, idFile.name, idFile.mimeType),
          workerOnboardingService.uploadLocalDocument('selfie', selfieFile.uri, selfieFile.name, selfieFile.mimeType),
        ]);
      } else {
        // Production: upload directly to S3/MinIO
        await Promise.all([
          workerOnboardingService.uploadToStorage(idUpload.upload_url!, idFile.uri, idFile.mimeType, idUpload.upload_headers),
          workerOnboardingService.uploadToStorage(selfieUpload.upload_url!, selfieFile.uri, selfieFile.mimeType, selfieUpload.upload_headers),
        ]);
        idKey = idUpload.s3_key!;
        selfieKey = selfieUpload.s3_key!;
      }

      await workerOnboardingService.submitIdentity(idKey, selfieKey);
      await authStorage.setOnboardingStep('identity_uploaded');
      setOnboardingStep('identity_uploaded');
      navigation.navigate('BuildProfile');
    } catch (err) {
      Alert.alert('Upload failed', getApiError(err, 'Could not upload documents. Please try again.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={baseStyles.root} edges={['top', 'bottom']}>
      <ScrollView
        contentContainerStyle={local.scroll}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <View style={baseStyles.progressTrack}>
          <View style={[baseStyles.progressFill, { width: '33%' }]} />
        </View>

        <Text style={baseStyles.heading}>Verify your identity</Text>
        <Text style={baseStyles.subheading}>
          We need a government-issued ID to keep everyone safe.
        </Text>

        {/* ── Govt ID ── */}
        <Pressable
          style={({ pressed }) => [local.uploadZone, pressed && local.uploadZonePressed]}
          onPress={pickId}
        >
          <UploadIcon size={28} color={C.brand} />
          <Text style={local.uploadTitle}>Upload govt ID</Text>
          <Text style={local.uploadHint}>Passport · Licence · National ID</Text>
        </Pressable>

        {idFile && (
          <FileRow file={idFile} onRemove={() => remove('id')} />
        )}

        {/* ── Selfie ── */}
        <Pressable
          style={({ pressed }) => [local.uploadZone, { marginTop: 12 }, pressed && local.uploadZonePressed]}
          onPress={pickSelfie}
        >
          <UploadIcon size={28} color={C.brand} />
          <Text style={local.uploadTitle}>Take / upload a selfie</Text>
          <Text style={local.uploadHint}>Must match your ID photo</Text>
        </Pressable>

        {selfieFile && (
          <FileRow file={selfieFile} onRemove={() => remove('selfie')} />
        )}

        <View style={{ height: 32 }} />

        <Pressable
          style={({ pressed }) => [
            baseStyles.button,
            canSubmit && baseStyles.buttonPrimary,
            (!canSubmit || isSubmitting) && baseStyles.buttonDisabled,
            pressed && canSubmit && baseStyles.buttonPressed,
          ]}
          onPress={handleNext}
          disabled={!canSubmit || isSubmitting}
        >
          {isSubmitting ? (
            <ActivityIndicator size="small" color={C.btnText} />
          ) : (
            <Text style={[baseStyles.buttonText, canSubmit && baseStyles.buttonTextPrimary]}>
              Next
            </Text>
          )}
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const local = StyleSheet.create({
  scroll: {
    paddingHorizontal: 26,
    paddingTop: 18,
    paddingBottom: 40,
  },
  uploadZone: {
    minHeight: 110,
    borderRadius: 12,
    borderWidth: 1.5,
    borderStyle: 'dashed',
    borderColor: C.border,
    backgroundColor: C.surface,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingHorizontal: 16,
  },
  uploadZonePressed: {
    backgroundColor: C.surfaceAlt,
    borderColor: C.brand,
  },
  uploadTitle: {
    color: C.ink,
    fontSize: 14,
    fontWeight: '700',
  },
  uploadHint: {
    color: C.muted,
    fontSize: 12,
  },

  // ── Uploaded file row ──
  fileRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginTop: 8,
    padding: 10,
    borderRadius: 10,
    backgroundColor: C.surfaceAlt,
    borderWidth: 1,
    borderColor: C.border,
  },
  fileThumb: {
    width: 40,
    height: 40,
    borderRadius: 6,
  },
  fileThumbPlaceholder: {
    width: 40,
    height: 40,
    borderRadius: 6,
    backgroundColor: C.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  fileThumbImage: {
    width: 40,
    height: 40,
    borderRadius: 6,
  },
  fileThumbText: {
    flex: 1,
    fontSize: 13,
    color: C.ink,
    fontWeight: '500',
  },
  fileThumbSub: {
    fontSize: 11,
    color: C.muted,
    marginTop: 2,
  },
  fileName: {
    flex: 1,
    fontSize: 13,
    color: '#17211a',
    fontWeight: '500',
  },
  fileRemove: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#f4f1e8',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
