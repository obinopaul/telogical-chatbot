'use client';

import { useState, useActionState, useEffect } from 'react';
import { signIn } from 'next-auth/react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { login, register, type LoginActionState, type RegisterActionState } from '../actions';
import { useRouter } from 'next/navigation';

export default function AuthPage() {
  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login');
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const router = useRouter();

  // Login form state
  const [loginState, loginAction] = useActionState<LoginActionState, FormData>(
    login,
    { status: 'idle' }
  );

  // Register form state
  const [registerState, registerAction] = useActionState<RegisterActionState, FormData>(
    register,
    { status: 'idle' }
  );

  // Handle successful auth
  useEffect(() => {
    if (loginState.status === 'success') {
      console.log('🎉 Login successful, redirecting to chatbot...');
      window.location.href = '/'; // Force full page redirect
    }
    if (registerState.status === 'success') {
      console.log('🎉 Registration successful, redirecting to chatbot...');
      window.location.href = '/'; // Force full page redirect
    }
  }, [loginState.status, registerState.status]);

  const handleGoogleSignIn = async () => {
    setIsGoogleLoading(true);
    try {
      await signIn('google', { callbackUrl: '/' });
    } catch (error) {
      console.error('Google sign-in error:', error);
    } finally {
      setIsGoogleLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome to Telogical
          </h1>
          <p className="text-gray-600">
            Your AI-powered telecommunications assistant
          </p>
        </div>

        {/* Main Form Card */}
        <div className="bg-white rounded-lg shadow-xl p-6">
          {/* Tab Buttons */}
          <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setActiveTab('login')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'login'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setActiveTab('register')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'register'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Create Account
            </button>
          </div>

          {/* Google Sign-In Button */}
          <Button
            onClick={handleGoogleSignIn}
            disabled={isGoogleLoading}
            variant="outline"
            className="w-full mb-4 py-2.5 border-gray-300 hover:bg-gray-50"
          >
            <svg className="size-5 mr-3" viewBox="0 0 24 24">
              <path
                fill="currentColor"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="currentColor"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="currentColor"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="currentColor"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            {isGoogleLoading ? 'Connecting...' : 'Continue with Google'}
          </Button>

          {/* Divider */}
          <div className="relative mb-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">or</span>
            </div>
          </div>

          {/* Login Form */}
          {activeTab === 'login' && (
            <form action={loginAction} className="space-y-4">
              {loginState.status === 'failed' && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                  Invalid email or password. Please try again.
                </div>
              )}
              {loginState.status === 'invalid_data' && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                  Please check your email and password format.
                </div>
              )}

              <div>
                <Label htmlFor="login-email" className="text-sm font-medium text-gray-700">
                  Email
                </Label>
                <Input
                  id="login-email"
                  name="email"
                  type="email"
                  required
                  className="mt-1"
                  placeholder="Enter your email"
                />
              </div>

              <div>
                <Label htmlFor="login-password" className="text-sm font-medium text-gray-700">
                  Password
                </Label>
                <Input
                  id="login-password"
                  name="password"
                  type="password"
                  required
                  className="mt-1"
                  placeholder="Enter your password"
                />
              </div>

              <Button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2.5"
                disabled={loginState.status === 'in_progress'}
              >
                {loginState.status === 'in_progress' ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>
          )}

          {/* Register Form */}
          {activeTab === 'register' && (
            <form action={registerAction} className="space-y-4">
              {registerState.status === 'failed' && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                  Registration failed. Please try again.
                </div>
              )}
              {registerState.status === 'user_exists' && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                  An account with this email already exists.
                </div>
              )}
              {registerState.status === 'invalid_data' && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                  Please check your information and try again.
                </div>
              )}

              <div>
                <Label htmlFor="register-name" className="text-sm font-medium text-gray-700">
                  Full Name
                </Label>
                <Input
                  id="register-name"
                  name="name"
                  type="text"
                  required
                  className="mt-1"
                  placeholder="Enter your full name"
                />
              </div>

              <div>
                <Label htmlFor="register-email" className="text-sm font-medium text-gray-700">
                  Email
                </Label>
                <Input
                  id="register-email"
                  name="email"
                  type="email"
                  required
                  className="mt-1"
                  placeholder="Enter your email"
                />
              </div>

              <div>
                <Label htmlFor="register-password" className="text-sm font-medium text-gray-700">
                  Password
                </Label>
                <Input
                  id="register-password"
                  name="password"
                  type="password"
                  required
                  minLength={6}
                  className="mt-1"
                  placeholder="Create a password (min 6 characters)"
                />
              </div>

              <div>
                <Label htmlFor="register-confirm-password" className="text-sm font-medium text-gray-700">
                  Confirm Password
                </Label>
                <Input
                  id="register-confirm-password"
                  name="confirmPassword"
                  type="password"
                  required
                  minLength={6}
                  className="mt-1"
                  placeholder="Retype your password"
                />
              </div>

              <Button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2.5"
                disabled={registerState.status === 'in_progress'}
              >
                {registerState.status === 'in_progress' ? 'Creating account...' : 'Create Account'}
              </Button>
            </form>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-6 text-sm text-gray-600">
          By continuing, you agree to our{' '}
          <a href="#" className="text-blue-600 hover:underline">
            Terms of Service
          </a>{' '}
          and{' '}
          <a href="#" className="text-blue-600 hover:underline">
            Privacy Policy
          </a>
        </div>
      </div>
    </div>
  );
}