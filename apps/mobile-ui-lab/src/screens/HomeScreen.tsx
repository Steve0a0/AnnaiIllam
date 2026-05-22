import React, { useState } from 'react';
import {
  View,
  YStack,
  XStack,
  Text,
  Card,
  Separator,
  Button,
  Input,
  Switch,
  ScrollView,
} from 'tamagui';
import { Pressable } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

type Props = {
  isDark: boolean;
  onToggleDark: () => void;
};

export default function HomeScreen({ isDark, onToggleDark }: Props) {
  const [count, setCount] = useState(0);
  const [inputValue, setInputValue] = useState('');
  const insets = useSafeAreaInsets();

  return (
    <View flex={1} backgroundColor="$background" paddingTop={insets.top}>
      <ScrollView>
        <YStack gap="$5" padding="$6">

          {/* Header */}
          <XStack justifyContent="space-between" alignItems="center">
            <YStack>
              <Text fontSize="$10" fontWeight="700" color="$color">UI Lab</Text>
              <Text fontSize="$3" color="$color9">Tamagui showcase</Text>
            </YStack>
            <XStack alignItems="center" gap="$2">
              <Text fontSize="$2" color="$color9">Dark</Text>
              <Switch size="$3" checked={isDark} onCheckedChange={() => onToggleDark()}>
                <Switch.Thumb animation="quick" />
              </Switch>
            </XStack>
          </XStack>

          <Separator />

          {/* Avatar + Badge Section */}
          <Card elevate bordered padding="$4">
            <Text fontSize="$6" fontWeight="600" color="$color" marginBottom="$3">
              Avatar &amp; Badges
            </Text>
            <XStack gap="$3" alignItems="center">
              <View
                width={50}
                height={50}
                borderRadius={25}
                backgroundColor="$blue9"
                alignItems="center"
                justifyContent="center"
              >
                <Text color="white" fontWeight="700" fontSize="$5">AI</Text>
              </View>
              <YStack>
                <Text fontWeight="600" color="$color">Annai Illam</Text>
                <XStack gap="$2" marginTop="$1">
                  <XStack
                    backgroundColor="$green3"
                    borderRadius="$2"
                    paddingHorizontal="$2"
                    paddingVertical="$1"
                  >
                    <Text color="$green10" fontSize="$2" fontWeight="600">Active</Text>
                  </XStack>
                  <XStack
                    borderWidth={1}
                    borderColor="$blue6"
                    borderRadius="$2"
                    paddingHorizontal="$2"
                    paddingVertical="$1"
                  >
                    <Text color="$blue10" fontSize="$2" fontWeight="600">v3</Text>
                  </XStack>
                </XStack>
              </YStack>
            </XStack>
          </Card>

          {/* Counter Section */}
          <Card elevate bordered padding="$4">
            <Text fontSize="$6" fontWeight="600" color="$color" marginBottom="$3">Counter</Text>
            <XStack justifyContent="center" alignItems="center" gap="$5">
              <Button
                size="$5"
                variant="outlined"
                theme="red"
                onPress={() => setCount(c => c - 1)}
              >
                −
              </Button>
              <View
                minWidth={64}
                alignItems="center"
                backgroundColor="$blue2"
                borderRadius="$4"
                paddingHorizontal="$4"
                paddingVertical="$2"
              >
                <Text fontSize="$10" fontWeight="700" color="$blue10">{count}</Text>
              </View>
              <Button
                size="$5"
                theme="green"
                onPress={() => setCount(c => c + 1)}
              >
                +
              </Button>
            </XStack>
            <Button
              chromeless
              marginTop="$3"
              alignSelf="center"
              onPress={() => setCount(0)}
            >
              Reset
            </Button>
          </Card>

          {/* Input Section */}
          <Card elevate bordered padding="$4">
            <Text fontSize="$6" fontWeight="600" color="$color" marginBottom="$3">Input</Text>
            <Input
              placeholder="Type something..."
              value={inputValue}
              onChangeText={setInputValue}
            />
            {inputValue.length > 0 && (
              <View
                marginTop="$2"
                padding="$3"
                backgroundColor="$blue2"
                borderRadius="$3"
              >
                <Text fontSize="$3" color="$blue10">{inputValue}</Text>
              </View>
            )}
          </Card>

          {/* Button Variants */}
          <Card elevate bordered padding="$4">
            <Text fontSize="$6" fontWeight="600" color="$color" marginBottom="$3">Button Variants</Text>
            <YStack gap="$2">
              <Button theme="blue">Solid Primary</Button>
              <Button variant="outlined">Outline Secondary</Button>
              <Button theme="green">Positive</Button>
              <Button theme="red">Negative</Button>
              <Button disabled opacity={0.5}>Disabled</Button>
            </YStack>
          </Card>

          {/* Pressable Cards */}
          <Text fontSize="$6" fontWeight="600" color="$color">Pressable Items</Text>
          {['Components', 'Theming', 'Animations'].map(item => (
            <Pressable key={item}>
              {({ pressed }) => (
                <Card elevate bordered padding="$4" opacity={pressed ? 0.7 : 1}>
                  <XStack justifyContent="space-between" alignItems="center">
                    <Text fontWeight="500" color="$color">{item}</Text>
                    <Text color="$color9">→</Text>
                  </XStack>
                </Card>
              )}
            </Pressable>
          ))}

        </YStack>
      </ScrollView>
    </View>
  );
}
