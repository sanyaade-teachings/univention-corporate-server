/*
 * Copyright 2011-2019 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/on",
	"umc/widgets/TextBox",
	"umc/widgets/_FormWidgetMixin",
	"put-selector/put"
], function(declare, lang, on, TextBox, _FormWidgetMixin, put) {
	return declare("umc.widgets.PasswordBox", [ TextBox, _FormWidgetMixin ], {
		type: 'password',

		buildRendering: function() {
			this.inherited(arguments);

			// HACK / WORKAROUND to prevent autocompletion
			//
			// autocomplete="off" is ignored by some
			// browsers due to https://www.w3.org/TR/html-design-principles/#priority-of-constituencies.
			// and autofill being and desired feature for users.
			// The workaround used in TextBox.js to set a random autocomplete value does not work
			// for type="password" (type="password" always prompts autocomplete)
			//
			// Catch the focus and then pass through to the actual input.
			// Likely that this workaround will be fixed in later chrome versions
			this.focusCatchNode = put('input.dijitInputInner[type="password"][tabIndex="-1"][style="position: absolute; opacity: 0;"]');
			on(this.focusCatchNode, 'focus', lang.hitch(this, 'focus'));
			put(this.focusNode, '-', this.focusCatchNode);
		}
	});
});
