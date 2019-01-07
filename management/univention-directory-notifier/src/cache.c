/*
 * Univention Directory Notifier
 *  cache.c
 *
 * Copyright 2004-2019 Univention GmbH
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
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <univention/debug.h>

#include "cache.h"
#include "notify.h"

extern long long notifier_cache_size;

static notify_cache_t *cache;
static int entry_min_pos = 0;
static int max_filled = 0;

int notifier_cache_init(unsigned long max_id) {
	int i;
	int count = 0;
	char *buffer;

	cache = calloc(notifier_cache_size, sizeof(notify_cache_t));
	entry_min_pos = 0;

	for (i = max_id - (notifier_cache_size - 1); i <= max_id; i++) {
		char *p, *pp;

		buffer = notify_transcation_get_one_dn(i);
		if (buffer == NULL) {
			max_filled = count;
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "max_filled = %d", max_filled);
			return 1;
		}

		sscanf(buffer, "%ld", &(cache[count].id));
		cache[count].command = buffer[strlen(buffer) - 1];
		p = index(buffer, ' ') + 1;
		pp = rindex(p, ' ');
		cache[count].dn = strndup(p, pp - p);

		free(buffer);
		count += 1;
	}

	max_filled = count;
	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "max_filled = %d", max_filled);

	return 0;
}

int notifier_cache_add(unsigned long id, char *dn, char cmd) {
	if (dn == NULL) {
		return 0;
	}

	if (max_filled < (notifier_cache_size - 1)) {
		max_filled += 1;

		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "Added to cache pos %d, id %ld", max_filled, id);

		cache[max_filled].id = id;
		cache[max_filled].dn = strdup(dn);
		cache[max_filled].command = cmd;
	} else {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "Added to cache pos %d, id %ld", entry_min_pos, id);

		cache[entry_min_pos].id = id;
		free(cache[entry_min_pos].dn);
		cache[entry_min_pos].dn = strdup(dn);
		cache[entry_min_pos].command = cmd;

		if (entry_min_pos < (notifier_cache_size - 1)) {
			entry_min_pos += 1;
		} else {
			entry_min_pos = 0;
		}
	}

	return 0;
}

char *notifier_cache_get(unsigned long id) {
	char *str;
	int i;

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "searching cache id = %ld", id);
	for (i = 0; i < max_filled; i++) {
		if (cache[i].id == id) {
			str = malloc(8192); /* FIXME */
			sprintf(str, "%ld %s %c", cache[i].id, cache[i].dn, cache[i].command);
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "string: [%s]", str);
			return str;
		}
	}

	return NULL;
}
