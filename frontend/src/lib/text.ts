/**
 * Insert `addition` into `current` at the textarea's caret position. If no
 * textarea ref is provided (or it's not focused), the addition is appended to
 * the end. A leading space is inserted automatically when needed so dictated
 * sentences don't run into existing text.
 *
 * Returns the new full string AND the caret position to set after the insert
 * so callers can preserve the cursor for subsequent dictation.
 */
export interface InsertResult {
    value: string;
    caret: number;
}

export function insertAtCaret(
    current: string,
    addition: string,
    textarea?: HTMLTextAreaElement | HTMLInputElement | null,
): InsertResult {
    const trimmedAddition = addition.trim();
    if (!trimmedAddition) {
        return { value: current, caret: textarea?.selectionStart ?? current.length };
    }

    const start = textarea?.selectionStart ?? current.length;
    const end = textarea?.selectionEnd ?? current.length;

    const before = current.slice(0, start);
    const after = current.slice(end);

    const needsLeadingSpace =
        before.length > 0 && !/\s$/.test(before) && !/^[\s.,;:!?)]/.test(trimmedAddition);
    const needsTrailingSpace = after.length > 0 && !/^\s/.test(after);

    const insertion =
        (needsLeadingSpace ? " " : "") +
        trimmedAddition +
        (needsTrailingSpace ? " " : "");

    const value = before + insertion + after;
    const caret = before.length + insertion.length;
    return { value, caret };
}
