import {
  CLEAR_UI,
  UPDATE_DIALOG_TEXT,
  UPDATE_DIALOG_TITLE,
  SET_DIALOG_VISIBILITY,
  SET_WORK_DIALOG_VISIBILITY,
  SET_WORK_DIALOG_INDEX,
  SET_EDUCATION_DIALOG_VISIBILITY,
  SET_EDUCATION_DIALOG_INDEX,
  SET_EDUCATION_DEGREE_LEVEL,
  SET_USER_PAGE_DIALOG_VISIBILITY,
  SET_SHOW_EDUCATION_DELETE_DIALOG,
  SET_SHOW_WORK_DELETE_DIALOG,
  SET_DELETION_INDEX,
  SET_PROFILE_STEP,
  SET_USER_MENU_OPEN,
  SET_SEARCH_FILTER_VISIBILITY,
  SET_EMAIL_DIALOG_VISIBILITY,
  SET_ENROLL_DIALOG_ERROR,
  SET_ENROLL_DIALOG_VISIBILITY,
  SET_ENROLL_MESSAGE,
  SET_ENROLL_SELECTED_PROGRAM,

  clearUI,
  updateDialogText,
  updateDialogTitle,
  setDialogVisibility,
  setWorkDialogVisibility,
  setWorkDialogIndex,
  setEducationDialogVisibility,
  setEducationDialogIndex,
  setEducationDegreeLevel,
  setUserPageDialogVisibility,
  setShowEducationDeleteDialog,
  setShowWorkDeleteDialog,
  setDeletionIndex,
  setProfileStep,
  setUserMenuOpen,
  setSearchFilterVisibility,
  setEmailDialogVisibility,
  setEnrollDialogError,
  setEnrollDialogVisibility,
  setEnrollMessage,
  setEnrollSelectedProgram,
} from '../actions/ui';
import { assertCreatedActionHelper } from './util';

describe('generated UI action helpers', () => {
  it('should create all action creators', () => {
    [
      [clearUI, CLEAR_UI],
      [updateDialogText, UPDATE_DIALOG_TEXT],
      [updateDialogTitle, UPDATE_DIALOG_TITLE],
      [setDialogVisibility, SET_DIALOG_VISIBILITY],
      [setWorkDialogVisibility, SET_WORK_DIALOG_VISIBILITY],
      [setWorkDialogIndex, SET_WORK_DIALOG_INDEX],
      [setEducationDialogVisibility, SET_EDUCATION_DIALOG_VISIBILITY],
      [setEducationDialogIndex, SET_EDUCATION_DIALOG_INDEX],
      [setEducationDegreeLevel, SET_EDUCATION_DEGREE_LEVEL],
      [setUserPageDialogVisibility, SET_USER_PAGE_DIALOG_VISIBILITY],
      [setShowEducationDeleteDialog, SET_SHOW_EDUCATION_DELETE_DIALOG],
      [setShowWorkDeleteDialog, SET_SHOW_WORK_DELETE_DIALOG],
      [setDeletionIndex, SET_DELETION_INDEX],
      [setProfileStep, SET_PROFILE_STEP],
      [setUserMenuOpen, SET_USER_MENU_OPEN],
      [setSearchFilterVisibility, SET_SEARCH_FILTER_VISIBILITY],
      [setEmailDialogVisibility, SET_EMAIL_DIALOG_VISIBILITY],
      [setEnrollDialogError, SET_ENROLL_DIALOG_ERROR],
      [setEnrollDialogVisibility, SET_ENROLL_DIALOG_VISIBILITY],
      [setEnrollMessage, SET_ENROLL_MESSAGE],
      [setEnrollSelectedProgram, SET_ENROLL_SELECTED_PROGRAM],
    ].forEach(assertCreatedActionHelper);
  });
});