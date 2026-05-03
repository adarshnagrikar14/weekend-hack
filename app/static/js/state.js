const state = {
  demandId: null,
  pipeline: null,
  samples: [],
};

const subscribers = new Set();

export function getState() {
  return state;
}

export function setState(patch) {
  Object.assign(state, patch);
  subscribers.forEach((callback) => callback(state));
}

export function subscribe(callback) {
  subscribers.add(callback);
  callback(state);
  return () => subscribers.delete(callback);
}
