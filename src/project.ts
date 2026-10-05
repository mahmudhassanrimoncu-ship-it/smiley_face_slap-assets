import {makeProject} from '@canvas-commons/core';
import '@fontsource/inter/400.css';
import '@fontsource/inter/500.css';
import '@fontsource/inter/600.css';
import '@fontsource/inter/700.css';
import '@fontsource/inter/800.css';

import intro from './scenes/intro?scene';
import overview from './scenes/overview?scene';
import evaporator from './scenes/evaporator?scene';
import compressor from './scenes/compressor?scene';
import condenser from './scenes/condenser?scene';
import valve from './scenes/valve?scene';
import energy from './scenes/energy?scene';
import door from './scenes/door?scene';
import final from './scenes/final?scene';

export default makeProject({
  name: 'how-a-refrigerator-works',
  scenes: [intro, overview, evaporator, compressor, condenser, valve, energy, door, final],
});
