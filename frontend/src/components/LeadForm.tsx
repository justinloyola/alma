import React, { useState } from 'react';
import axios from 'axios';

interface LeadFormData {
  firstName: string;
  lastName: string;
  email: string;
  resume: File | null;
}

const LeadForm: React.FC = () => {
  const [formData, setFormData] = useState<LeadFormData>({
    firstName: '',
    lastName: '',
    email: '',
    resume: null,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFormData(prev => ({
        ...prev,
        resume: e.target.files![0],
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.resume) {
      setSubmitStatus({
        success: false,
        message: 'Please upload a resume file.',
      });
      return;
    }

    setIsSubmitting(true);
    setSubmitStatus(null);

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('first_name', formData.firstName);
      formDataToSend.append('last_name', formData.lastName);
      formDataToSend.append('email', formData.email);
      // Phone field has been removed
      formDataToSend.append('resume', formData.resume);

      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '';
      const baseUrl = apiBaseUrl || '';

      const response = await axios.post(`${baseUrl}/api/v1/leads`, formDataToSend, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setSubmitStatus({
        success: true,
        message: 'Lead submitted successfully!',
      });

      // Reset form
      setFormData({
        firstName: '',
        lastName: '',
        email: '',
        resume: null,
      });
    } catch (error: any) {
      console.error('Error submitting lead:', error);
      let errorMessage = 'Failed to submit lead. Please try again.';

      if (error?.response?.data?.detail) {
        errorMessage = String(error.response.data.detail);
      } else if (error?.message) {
        errorMessage = error.message;
      }

      setSubmitStatus({
        success: false,
        message: errorMessage,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-8 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Submit Your Information</h2>

      {submitStatus && (
        <div className={`mb-4 p-3 rounded ${submitStatus.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
          {submitStatus.message}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="firstName" className="block text-sm font-medium text-gray-700">
            First Name *
          </label>
          <input
            type="text"
            id="firstName"
            name="firstName"
            required
            value={formData.firstName}
            onChange={handleChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>

        <div>
          <label htmlFor="lastName" className="block text-sm font-medium text-gray-700">
            Last Name *
          </label>
          <input
            type="text"
            id="lastName"
            name="lastName"
            required
            value={formData.lastName}
            onChange={handleChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            Email *
          </label>
          <input
            type="email"
            id="email"
            name="email"
            required
            value={formData.email}
            onChange={handleChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>

<div>
          <label htmlFor="resume" className="block text-sm font-medium text-gray-700">
            Resume (PDF, DOC, DOCX) *
          </label>
          <input
            type="file"
            id="resume"
            name="resume"
            accept=".pdf,.doc,.docx"
            onChange={handleFileChange}
            className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
        </div>

        <div className="pt-2">
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Submitting...' : 'Submit'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default LeadForm;
